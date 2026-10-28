import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.io.*;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * ForeverWorld pre-launch helper. Runs packwiz-installer (through packwiz-installer-bootstrap.jar, without its window) to update
 * the instance from the pack. CurseForge mods whose authors block third-party downloads make the installer stop and print where
 * to get them; those are listed here with direct /download/ links, picked up from the Downloads folder as they arrive (or saved
 * straight into the mods folder), and the installer is run again until the pack is complete.
 *
 * Before that it asks for the launch mode (Mode): which of the pack's optional performance mods to install. packwiz-installer cannot
 * ask without its window and turns every optional mod on, so PackHelper writes the choice into its packwiz.json instead.
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

	private static final String C2ME = "mods/c2me.pw.toml", C2ME_OPENCL = "mods/c2me-ocl.pw.toml", DISTANT_HORIZONS = "mods/distant-horizons.pw.toml";
	/** The optional mods (pack paths of their .pw.toml) the modes switch; every other optional mod is left as the installer set it. */
	private static final List<String> MODE_FILES = List.of(C2ME, C2ME_OPENCL, DISTANT_HORIZONS);
	private static final Path MODE_FILE = Paths.get("foreverworld-mode.txt");
	private static final Path MANIFEST = Paths.get("packwiz.json");
	private static final int COUNTDOWN_SECONDS = 8;

	private enum Mode
	{
		HEAVY("Heavy", "Recommended for a high-end CPU + GPU",
				"Distant Horizons, plus C2ME and its OpenCL module: much faster world generation in singleplayer, on the graphics card"
						+ " when it supports OpenCL. The OpenCL module is still an alpha.", C2ME, C2ME_OPENCL, DISTANT_HORIZONS),
		LITE("Lite", "Recommended for the official server",
				"Distant Horizons, which draws the far-off terrain the tall world is hard to play without. C2ME is off.", DISTANT_HORIZONS),
		SUPER_LITE("Super Lite", "For computers with very limited resources",
				"No Distant Horizons and no C2ME: the least memory and CPU, but only nearby terrain is drawn.");

		final String title, recommendation, details;
		final Set<String> enabled;

		Mode(String title, String recommendation, String details, String... enabled)
		{
			this.title = title;
			this.recommendation = recommendation;
			this.details = details;
			this.enabled = Set.of(enabled);
		}
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
		final Mode mode = chooseMode();
		if (mode == null)
		{
			System.exit(1);
		}
		applyMode(mode);
		int modePasses = 0;
		while (true)
		{
			final List<String> output = new ArrayList<>();
			final int code = runInstaller(packUrl, output);
			if (code == 0)
			{
				// a first install (or a newly optional mod) arrives with everything on: apply the mode and let the installer remove the rest
				if (modePasses++ < 2 && applyMode(mode))
				{
					continue;
				}
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

	/**
	 * Asks for the launch mode. The last mode is preselected and starts by itself after a few seconds; the first launch waits for a
	 * choice. Returns null when the player cancels the launch.
	 */
	private static Mode chooseMode() throws Exception
	{
		Mode saved = null;
		try
		{
			saved = Mode.valueOf(Files.readString(MODE_FILE).trim());
		}
		catch (IOException | IllegalArgumentException ignored)
		{
		}
		if (GraphicsEnvironment.isHeadless())
		{
			return saved != null ? saved : Mode.LITE;
		}
		final Mode preselected = saved != null ? saved : Mode.LITE;
		final boolean countdown = saved != null;
		final AtomicReference<Mode> result = new AtomicReference<>();
		final CountDownLatch chosen = new CountDownLatch(1);
		final JFrame[] frame = new JFrame[1];
		SwingUtilities.invokeAndWait(() -> {
			try
			{
				UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
			}
			catch (Exception ignored)
			{
			}
			final JFrame f = new JFrame("ForeverWorld: launch mode");
			f.setDefaultCloseOperation(WindowConstants.DO_NOTHING_ON_CLOSE);
			f.addWindowListener(new java.awt.event.WindowAdapter()
			{
				@Override
				public void windowClosing(java.awt.event.WindowEvent e)
				{
					chosen.countDown();
				}
			});
			final JPanel root = new JPanel(new BorderLayout(0, 10));
			root.setBorder(new EmptyBorder(12, 12, 12, 12));
			root.add(new JLabel("<html>Choose how much the game runs. You can change it at every launch.</html>"), BorderLayout.NORTH);
			final JPanel modes = new JPanel(new GridLayout(0, 1, 0, 8));
			for (Mode mode : Mode.values())
			{
				final JButton button = new JButton("<html><div style='width:430px'><b>" + mode.title + "</b> &nbsp;·&nbsp; <i>" + mode.recommendation
						+ "</i><br>" + mode.details + "</div></html>");
				button.setHorizontalAlignment(SwingConstants.LEFT);
				if (mode == preselected)
				{
					button.setBorder(BorderFactory.createCompoundBorder(BorderFactory.createLineBorder(new Color(0x2E7D32), 2),
							new EmptyBorder(6, 8, 6, 8)));
					f.getRootPane().setDefaultButton(button);
				}
				button.addActionListener(e -> {
					result.set(mode);
					chosen.countDown();
				});
				modes.add(button);
			}
			root.add(modes, BorderLayout.CENTER);
			final JPanel bottom = new JPanel(new BorderLayout());
			final JLabel status = new JLabel(countdown ? "" : "First launch: pick a mode. Lite is recommended.");
			bottom.add(status, BorderLayout.CENTER);
			final JButton cancel = new JButton("Cancel launch");
			cancel.addActionListener(e -> chosen.countDown());
			bottom.add(cancel, BorderLayout.EAST);
			root.add(bottom, BorderLayout.SOUTH);
			if (countdown)
			{
				final int[] left = { COUNTDOWN_SECONDS };
				status.setText("Starting " + preselected.title + " in " + left[0] + " s");
				final javax.swing.Timer timer = new javax.swing.Timer(1000, null);
				timer.addActionListener(e -> {
					if (--left[0] <= 0)
					{
						timer.stop();
						result.compareAndSet(null, preselected);
						chosen.countDown();
					}
					else
					{
						status.setText("Starting " + preselected.title + " in " + left[0] + " s");
					}
				});
				timer.start();
			}
			f.setContentPane(root);
			f.pack();
			f.setLocationRelativeTo(null);
			f.setVisible(true);
			frame[0] = f;
		});
		chosen.await();
		SwingUtilities.invokeAndWait(() -> frame[0].dispose());
		final Mode mode = result.get();
		if (mode != null)
		{
			try
			{
				Files.writeString(MODE_FILE, mode.name());
			}
			catch (IOException e)
			{
				System.out.println("[PackHelper] could not save the launch mode: " + e);
			}
			System.out.println("[PackHelper] launch mode: " + mode.title);
		}
		return mode;
	}

	/**
	 * Writes the mode's on/off choices into packwiz-installer's packwiz.json. When one changed, the saved pack hashes are cleared so
	 * the next installer run checks every file again and downloads or deletes the switched mods. Returns whether anything changed.
	 */
	@SuppressWarnings("unchecked")
	private static boolean applyMode(Mode mode)
	{
		if (!Files.isRegularFile(MANIFEST))
		{
			return false;
		}
		try
		{
			final Map<String, Object> manifest = (Map<String, Object>) new Json(Files.readString(MANIFEST)).value();
			final Map<String, Object> cached = (Map<String, Object>) manifest.get("cachedFiles");
			if (cached == null)
			{
				return false;
			}
			boolean changed = false;
			for (String file : MODE_FILES)
			{
				final Map<String, Object> entry = (Map<String, Object>) cached.get(file);
				final Boolean wanted = mode.enabled.contains(file);
				if (entry != null && !wanted.equals(entry.get("optionValue")))
				{
					entry.put("optionValue", wanted);
					changed = true;
				}
			}
			if (changed)
			{
				manifest.put("packFileHash", null);
				manifest.put("indexFileHash", null);
				Files.writeString(MANIFEST, Json.write(manifest));
				System.out.println("[PackHelper] switched optional mods for " + mode.title);
			}
			return changed;
		}
		catch (IOException | RuntimeException e)
		{
			System.out.println("[PackHelper] could not apply the launch mode: " + e);
			return false;
		}
	}

	/** Just enough JSON for packwiz.json: objects keep their key order, numbers are kept as written. */
	private static final class Json
	{
		private final String text;
		private int at;

		Json(String text)
		{
			this.text = text;
		}

		Object value()
		{
			skip();
			final char c = this.text.charAt(this.at);
			if (c == '{')
			{
				final Map<String, Object> map = new LinkedHashMap<>();
				this.at++;
				skip();
				if (this.text.charAt(this.at) == '}')
				{
					this.at++;
					return map;
				}
				while (true)
				{
					skip();
					final String key = string();
					skip();
					expect(':');
					map.put(key, value());
					skip();
					if (this.text.charAt(this.at++) == '}')
					{
						return map;
					}
				}
			}
			if (c == '[')
			{
				final List<Object> list = new ArrayList<>();
				this.at++;
				skip();
				if (this.text.charAt(this.at) == ']')
				{
					this.at++;
					return list;
				}
				while (true)
				{
					list.add(value());
					skip();
					if (this.text.charAt(this.at++) == ']')
					{
						return list;
					}
				}
			}
			if (c == '"')
			{
				return string();
			}
			for (String word : new String[] { "true", "false", "null" })
			{
				if (this.text.startsWith(word, this.at))
				{
					this.at += word.length();
					return word.equals("null") ? null : Boolean.valueOf(word);
				}
			}
			final int start = this.at;
			while (this.at < this.text.length() && "+-0123456789.eE".indexOf(this.text.charAt(this.at)) >= 0)
			{
				this.at++;
			}
			if (start == this.at)
			{
				throw new IllegalArgumentException("unexpected '" + c + "' at " + start);
			}
			return new java.math.BigDecimal(this.text.substring(start, this.at));
		}

		private String string()
		{
			expect('"');
			final StringBuilder out = new StringBuilder();
			while (true)
			{
				final char c = this.text.charAt(this.at++);
				if (c == '"')
				{
					return out.toString();
				}
				if (c != '\\')
				{
					out.append(c);
					continue;
				}
				final char e = this.text.charAt(this.at++);
				switch (e)
				{
					case 'n' -> out.append('\n');
					case 't' -> out.append('\t');
					case 'r' -> out.append('\r');
					case 'b' -> out.append('\b');
					case 'f' -> out.append('\f');
					case 'u' -> {
						out.append((char) Integer.parseInt(this.text.substring(this.at, this.at + 4), 16));
						this.at += 4;
					}
					default -> out.append(e);
				}
			}
		}

		private void expect(char c)
		{
			if (this.text.charAt(this.at++) != c)
			{
				throw new IllegalArgumentException("expected '" + c + "' at " + (this.at - 1));
			}
		}

		private void skip()
		{
			while (this.at < this.text.length() && Character.isWhitespace(this.text.charAt(this.at)))
			{
				this.at++;
			}
		}

		static String write(Object value)
		{
			final StringBuilder out = new StringBuilder();
			write(value, out);
			return out.toString();
		}

		@SuppressWarnings("unchecked")
		private static void write(Object value, StringBuilder out)
		{
			if (value instanceof Map<?, ?> map)
			{
				out.append('{');
				boolean first = true;
				for (Map.Entry<String, Object> entry : ((Map<String, Object>) map).entrySet())
				{
					out.append(first ? "" : ",");
					first = false;
					quote(entry.getKey(), out);
					out.append(':');
					write(entry.getValue(), out);
				}
				out.append('}');
			}
			else if (value instanceof List<?> list)
			{
				out.append('[');
				for (int i = 0; i < list.size(); i++)
				{
					out.append(i == 0 ? "" : ",");
					write(list.get(i), out);
				}
				out.append(']');
			}
			else if (value instanceof String string)
			{
				quote(string, out);
			}
			else
			{
				out.append(value);
			}
		}

		private static void quote(String string, StringBuilder out)
		{
			out.append('"');
			for (char c : string.toCharArray())
			{
				switch (c)
				{
					case '"' -> out.append("\\\"");
					case '\\' -> out.append("\\\\");
					case '\n' -> out.append("\\n");
					case '\r' -> out.append("\\r");
					case '\t' -> out.append("\\t");
					default -> {
						if (c < 0x20)
						{
							out.append(String.format("\\u%04x", (int) c));
						}
						else
						{
							out.append(c);
						}
					}
				}
			}
			out.append('"');
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
