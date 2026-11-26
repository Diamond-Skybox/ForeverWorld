// Immersive Aircraft x Immersive Engineering: aircraft burn liquid fuel (#iaie:fuel: IE biodiesel, Immersive Petroleum diesel and
// kerosene, PneumaticCraft and TFMG diesel and kerosene) from a fuel tank placed in the fuel slot. Only the IE Metal Barrel was a
// tank, and a bucket does nothing. The add-on reads the fuel from IE's own item fluid storage, so only IE items can be tanks;
// the Jerrycan (10 buckets) and the Wooden Barrel (12, like the Metal Barrel) store it the same way.
ServerEvents.tags('item', event => {
	event.add('iaie:fuel_tanks', ['immersiveengineering:jerrycan', 'immersiveengineering:wooden_barrel'])
})
