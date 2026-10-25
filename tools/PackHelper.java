import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.io.*;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * ForeverWorld pre-launch helper. Runs packwiz-installer (through packwiz-installer-bootstrap.jar, without its window) to update
 * the instance from the pack. CurseForge mods whose authors block third-party downloads make the installer stop and print where
 * to get them; those are listed here with direct /download/ links, picked up from the Downloads folder as they arrive (or saved
 * straight into the mods folder), and the installer is run again until the pack is complete.
 *
 * Prism pre-launch command (run from the instance's minecraft folder):
 *   "$INST_JAVA" -jar PackHelper.jar https://raw.githubusercontent.com/Diamond-Skybox/ForeverWorld/main/pack.toml
 * Exit code 0 starts the game, anything else stops the launch. Shipped compiled (Prism's bundled Java is a JRE, which cannot run a
 * .java file directly); build with tools/build-packhelper.sh.
 */
public final class PackHelper
{
	private static final Pattern MANUAL = Pattern.compile("Please go to (\\S+) and save this file to (.+?)\\s*$");
	private static final Pattern NAME = Pattern.compile("^(.+?): java\\.lang\\.Exception: This mod is excluded from the CurseForge API");
	private static final Pattern FILES_LINK = Pattern.compile("/files/(\\d+)/?$");
	private static final String[] PARTIAL = { ".part", ".crdownload", ".download", ".tmp", ".partial" };

	private record Missing(String name, String url, Path target)
	{
	}

	public static void main(String[] args) throws Exception
	{
		if (args.length < 1)
		{
			System.err.println("usage: PackHelper.java <pack.toml URL> [--downloads <folder>]");
			System.exit(2);
		}
		preloadOwnClasses();
		final String packUrl = args[0];
		final List<Path> downloadDirs = new ArrayList<>();
		for (int i = 1; i < args.length; i++)
		{
			if (args[i].equals("--downloads") && i + 1 < args.length)
			{
				downloadDirs.add(Paths.get(args[++i]));
			}
		}
		if (downloadDirs.isEmpty())
		{
			downloadDirs.addAll(defaultDownloadDirs());
		}
		while (true)
		{
			final List<String> output = new ArrayList<>();
			final int code = runInstaller(packUrl, output);
			if (code == 0)
			{
				System.exit(0);
			}
			final List<Missing> missing = parseMissing(output);
			if (missing.isEmpty())
			{
				System.exit(askAfterError(output) ? 0 : code);
			}
			final int choice = collect(missing, downloadDirs);
			if (choice != RETRY)
			{
				System.exit(choice == START ? 0 : 1);
			}
		}
	}

	/**
	 * PackHelper.jar is itself a pack file, so the installer it runs may replace it; every class is loaded up front so the rest of
	 * this run never reads the jar again.
	 */
	private static void preloadOwnClasses()
	{
		try
		{
			final Path self = Paths.get(PackHelper.class.getProtectionDomain().getCodeSource().getLocation().toURI());
			if (!Files.isRegularFile(self))
			{
				return;
			}
			try (java.util.jar.JarFile jar = new java.util.jar.JarFile(self.toFile()))
			{
				for (java.util.jar.JarEntry entry : Collections.list(jar.entries()))
				{
					if (entry.getName().endsWith(".class"))
					{
						Class.forName(entry.getName().replace('/', '.').replace(".class", ""), false, PackHelper.class.getClassLoader());
					}
				}
			}
		}
		catch (Exception | LinkageError e)
		{
			System.out.println("[PackHelper] could not preload classes: " + e);
		}
	}

	/** Runs the bootstrap without its window, echoing its output to the console (Prism's log) and keeping it for parsing. */
	private static int runInstaller(String packUrl, List<String> output) throws IOException, InterruptedException
	{
		final String java = ProcessHandle.current().info().command().orElse("java");
		final Process process = new ProcessBuilder(java, "-jar", "packwiz-installer-bootstrap.jar", "-g", packUrl)
				.redirectErrorStream(true).start();
		try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8)))
		{
			String line;
			while ((line = reader.readLine()) != null)
			{
				System.out.println(line);
				output.add(line);
			}
		}
		return process.waitFor();
	}

	private static List<Missing> parseMissing(List<String> output)
	{
		final List<Missing> missing = new ArrayList<>();
		final Set<Path> seen = new HashSet<>();
		String name = null;
		for (String line : output)
		{
			final Matcher n = NAME.matcher(line);
			if (n.find())
			{
				name = n.group(1);
			}
			final Matcher m = MANUAL.matcher(line);
			if (m.find())
			{
				final Path target = Paths.get(m.group(2));
				if (seen.add(target))
				{
					missing.add(new Missing(name != null ? name : target.getFileName().toString(), directLink(m.group(1)), target));
				}
				name = null;
			}
		}
		return missing;
	}

	/** CurseForge's file page (…/files/<id>) becomes its direct download (…/download/<id>). */
	private static String directLink(String url)
	{
		return FILES_LINK.matcher(url).replaceFirst("/download/$1");
	}

	private static List<Path> defaultDownloadDirs()
	{
		final Set<Path> dirs = new LinkedHashSet<>();
		final Path home = Paths.get(System.getProperty("user.home"));
		final Path userDirs = home.resolve(".config/user-dirs.dirs");
		if (Files.isReadable(userDirs))
		{
			try
			{
				for (String line : Files.readAllLines(userDirs))
				{
					if (line.startsWith("XDG_DOWNLOAD_DIR="))
					{
						dirs.add(Paths.get(line.substring(line.indexOf('=') + 1).replace("\"", "").replace("$HOME", home.toString())));
					}
				}
			}
			catch (IOException ignored)
			{
			}
		}
		dirs.add(home.resolve("Downloads"));
		return new ArrayList<>(dirs);
	}

	private static final int RETRY = 0, START = 1, CANCEL = 2;

	/** Shows the missing mods and waits until all of them are in place (then RETRY), or the player starts or cancels anyway. */
	private static int collect(List<Missing> missing, List<Path> downloadDirs) throws Exception
	{
		final AtomicInteger result = new AtomicInteger(-1);
		final JLabel[] status = new JLabel[missing.size()];
		final JFrame[] frame = new JFrame[1];
		SwingUtilities.invokeAndWait(() -> {
			try
			{
				UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
			}
			catch (Exception ignored)
			{
			}
			final JFrame f = new JFrame("ForeverWorld: mods to download by hand");
			f.setDefaultCloseOperation(WindowConstants.DO_NOTHING_ON_CLOSE);
			f.addWindowListener(new java.awt.event.WindowAdapter()
			{
				@Override
				public void windowClosing(java.awt.event.WindowEvent e)
				{
					result.compareAndSet(-1, CANCEL);
				}
			});
			final JPanel root = new JPanel(new BorderLayout(0, 10));
			root.setBorder(new EmptyBorder(12, 12, 12, 12));
			root.add(new JLabel("<html>These mods' authors don't allow launchers to download them. Click <b>Download</b> for each one;"
					+ " the files are picked up from your Downloads folder automatically.<br>If your browser saves elsewhere, put them in: "
					+ missing.get(0).target().getParent() + "</html>"), BorderLayout.NORTH);
			final JPanel list = new JPanel(new GridBagLayout());
			final GridBagConstraints c = new GridBagConstraints();
			c.insets = new Insets(3, 4, 3, 4);
			c.anchor = GridBagConstraints.WEST;
			for (int i = 0; i < missing.size(); i++)
			{
				final Missing m = missing.get(i);
				c.gridy = i;
				c.gridx = 0;
				c.weightx = 1;
				list.add(new JLabel(m.name()), c);
				c.gridx = 1;
				c.weightx = 0;
				final JButton download = new JButton("Download");
				download.addActionListener(e -> open(m.url()));
				list.add(download, c);
				c.gridx = 2;
				status[i] = new JLabel("waiting");
				list.add(status[i], c);
			}
			root.add(new JScrollPane(list), BorderLayout.CENTER);
			final JPanel buttons = new JPanel(new FlowLayout(FlowLayout.RIGHT));
			final JButton all = new JButton("Open all links");
			all.addActionListener(e -> missing.forEach(m -> open(m.url())));
			final JButton folder = new JButton("Open mods folder");
			folder.addActionListener(e -> open(missing.get(0).target().getParent().toUri().toString()));
			final JButton start = new JButton("Start without them");
			start.addActionListener(e -> result.compareAndSet(-1, START));
			final JButton cancel = new JButton("Cancel launch");
			cancel.addActionListener(e -> result.compareAndSet(-1, CANCEL));
			buttons.add(all);
			buttons.add(folder);
			buttons.add(start);
			buttons.add(cancel);
			root.add(buttons, BorderLayout.SOUTH);
			f.setContentPane(root);
			f.setSize(720, Math.min(160 + 34 * missing.size(), 640));
			f.setLocationRelativeTo(null);
			f.setVisible(true);
			frame[0] = f;
		});
		final Map<Path, Long> lastSize = new HashMap<>();
		while (result.get() < 0)
		{
			int done = 0;
			for (int i = 0; i < missing.size(); i++)
			{
				final Missing m = missing.get(i);
				final boolean have = Files.isRegularFile(m.target()) || pickUp(m.target(), downloadDirs, lastSize);
				final int index = i;
				SwingUtilities.invokeLater(() -> status[index].setText(have ? "✔ found" : "waiting"));
				if (have)
				{
					done++;
				}
			}
			if (done == missing.size())
			{
				result.compareAndSet(-1, RETRY);
				break;
			}
			Thread.sleep(1000);
		}
		SwingUtilities.invokeAndWait(() -> frame[0].dispose());
		return result.get();
	}

	/** Copies the file into place once it is in a Downloads folder and has stopped growing (the browser finished writing it). */
	private static boolean pickUp(Path target, List<Path> downloadDirs, Map<Path, Long> lastSize)
	{
		final String fileName = target.getFileName().toString();
		for (Path dir : downloadDirs)
		{
			final Path candidate = dir.resolve(fileName);
			try
			{
				if (!Files.isRegularFile(candidate))
				{
					continue;
				}
				final long size = Files.size(candidate);
				final Long previous = lastSize.put(candidate, size);
				if (previous == null || previous != size || size == 0 || partialExists(dir, fileName))
				{
					continue;
				}
				Files.createDirectories(target.getParent());
				Files.copy(candidate, target, StandardCopyOption.REPLACE_EXISTING);
				System.out.println("[PackHelper] took " + candidate + " -> " + target);
				return true;
			}
			catch (IOException e)
			{
				System.out.println("[PackHelper] could not take " + candidate + ": " + e);
			}
		}
		return false;
	}

	private static boolean partialExists(Path dir, String fileName)
	{
		for (String suffix : PARTIAL)
		{
			if (Files.exists(dir.resolve(fileName + suffix)))
			{
				return true;
			}
		}
		return false;
	}

	private static void open(String url)
	{
		try
		{
			if (Desktop.isDesktopSupported() && Desktop.getDesktop().isSupported(Desktop.Action.BROWSE))
			{
				Desktop.getDesktop().browse(URI.create(url));
				return;
			}
		}
		catch (Exception ignored)
		{
		}
		final String os = System.getProperty("os.name").toLowerCase(Locale.ROOT);
		final String[] command = os.contains("win") ? new String[] { "rundll32", "url.dll,FileProtocolHandler", url }
				: os.contains("mac") ? new String[] { "open", url } : new String[] { "xdg-open", url };
		try
		{
			new ProcessBuilder(command).start();
		}
		catch (IOException e)
		{
			System.out.println("[PackHelper] could not open " + url + ": " + e);
		}
	}

	/** The installer failed for another reason (network, CurseForge down...): let the player retry by relaunching, or play anyway. */
	private static boolean askAfterError(List<String> output) throws Exception
	{
		final String tail = String.join("\n", output.subList(Math.max(0, output.size() - 15), output.size()));
		final int[] answer = new int[1];
		SwingUtilities.invokeAndWait(() -> answer[0] = JOptionPane.showOptionDialog(null,
				"The pack could not be updated:\n\n" + tail + "\n\nStart the game with the mods already installed?",
				"ForeverWorld update failed", JOptionPane.YES_NO_OPTION, JOptionPane.WARNING_MESSAGE, null,
				new Object[] { "Start anyway", "Cancel launch" }, "Cancel launch"));
		return answer[0] == 0;
	}
}
