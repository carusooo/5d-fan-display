# 5D Hologram Display Controller

This repo contains a driver for a POV display device with 160 LEDs, similar to hologram fans. Here's an [example](https://www.alibaba.com/product-detail/hologram-projector-3D-fan-360-cylinder_1600725569818.html?spm=a2700.shop_plser.41413.9.15e7470fLTpMZq).


To use this repo:

- Check out the repo using 
    `git clone https://github.com/carusooo/5d-fan-display`

- `cd` to the root directory
    `cd 5d-fan-display `

- Connect to the WiFi of the fan, it should start with `3D-...`

- Run the python script
```shell
    python fan_cmd.py turn_off
```


- To see more command, you can run the python script
```shell
    python fan_cmd.py --help
```


## To-Dos

- [ ] Support listing out the playing files
- [ ] Support deleting files
- [ ] Automate the conversion of images
- [ ] Create a script that will run a clock or similar appliance on the display


## Credits

Huge thanks to @jnweiger's [work](https://github.com/jnweiger/led-hologram-propeller/tree/master), and the support people at [CZ-Yama](https://gzyama.en.alibaba.com/contactinfo.html?spm=a2700.shop_index.88.78) for sending me an APK to de-compile :) 
