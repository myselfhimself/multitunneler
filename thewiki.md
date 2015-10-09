[Edit this page](http://code.google.com/p/multitunneler/w/edit/thewiki)

TODO http://kb.digium.com/entry/73/ => zapata.conf => uncomment relaxdtm=yes

# Documentation #
## Developer documentation ##

### Source code origins ###
This project is a highly modified version of  the `forward.py` example script from the [Python Paramiko library](http://www.lag.net/paramiko/).

On the one hand, the forward.py script allows to setup a single channel through an single SSH tunnel and is configure over command line options.

On the other hand, multi\_tunneler allows to have multiple channels through a single SSH tunnel with configuration parsed from a JSON file and login+password hardcodable either in the latter file or in a provided\_login\_info.py file dedicated just for that.

The forward.py script was licensed under a GPL version. Thus a GPL license has been kept for the multi\_tunneler project.

### Source code languages ###
  * [Python 2.5+](http://www.python.org) for the .py scripts
  * [JSON](http://www.json.org) for the tunnels\_conf.json config file which must stand in the same folder as the python executable

### Libraries ###
The multi\_tunneler.py executable needs the following two libraries to work `(1)`:
  * either of the [simplejson](http://pypi.python.org/pypi/simplejson) (version 2.0.7) or [json](http://docs.python.org/library/json.html) (builtin and renamed from simplejson from python2.6) python library. This library helps to transform python types (dictionary,lists,strings and integers] from/to JSON string format.
  * the [Paramiko Python library](http://www.lag.net/paramiko/) in versions higher or lower than 1.7.4. Paramiko is a pure-python, cross-platform, sockets-based SSH2 implementation.

`(1)`note: those two libraries are embedded/ship with every item of the [Downloads section](http://code.google.com/p/multitunneler/wiki/downloads?tm=2) so you don't need to install them.

## End-user documentation ##

### Platforms for running multi\_tunneler ###
  * currently Windows and Linux. multi\_tunneler can run everywhere where python is installed, just get the source archive, extract it and run edit the code you want.
  * despite that, emphasis as been put on making the shipped program as whole depend on nothing (not any ssh executable nor a python installation).


### Running the multi\_tunneler ###

To run the multi\_tunneler application, you must go to its executable's folder and:
  1. modify the tunnels\_conf.json file to put your tunneling gate server and desired tunnels information (IP or hostnames and ports...)
  1. optionally, create or edit a provided\_login\_info.py file to put your login & password for the tunneling gate saver.
  1. execute the `multi_tunneler.py`(needs Python2.5/2.6 installed) or the `multi_tunneler`/`multi_tunneler.exe` executable depending on your platform.

### Unixes only - Running as root/sudo to kill process occupying ports ###
On Unix systems only (Linux, MacOS, BSD... Solaris), if you run the multi\_tunneler executable with option `-k`, the processes occupying ports that we want to have opened for ourselves will be killed from a root/sudo-/fakeroot account.
If you are not root, the multi\_tunneler will run the kill commands as sudo and you must type a password.

### Editing the 2 connection options' configuration files ###
#### tunnels\_conf.json ####
An external JSON file is located in the same folder as the executable.

That file is used to setup of the gate host's hostname and port, destination host's hostname, and correspondance between ports to open locally and ports to reach on destination host.

**_To have detailed help on this .json file's possible fields, just open and take a look at that file's `"help":` fields at the top._**

### skipping password typing to connect to the gate ###
To avoid typing your login and password for the gate server at each run, you can edit either of the `provided_login_info.py` or `tunnels_conf.json` files.

#### provided\_login\_info.py login+password module variables ####
Reopen or create a file `provided_login_info.py` in your `multi_tuneler` executable folder with content:
```
username="gateUsername"
password="gatePassword"
```

_Note:_ Editing/creating the `provided_login_info.py` file is interesting to make an executable embed and thus "hide" a login+password. Indeed, python "compilers" such as [Py2Exe](http://www.py2exe.org/) and [PyInstaller](http://pyinstaller.python-hosting.com/) most of the time provide the option to embed all imported modules(hence our .py file) into a single executable file.

#### tunnels\_conf.json login+password fields ####
Alternatively from before, a login and password can added into the JSON file's gate's dictionary structure:
```
[...]
"gate": {
    "hostname":"someIpOrHostname.com",
    "port":AnInteger,
    "username":"gateUsername",
    "password":"gatePassword"
    },
[...]
```



## Known issues ##
### Running from a different folder ###
When executed from a different folder as the one it is located in, the multi\_tunneler(.py) executable _may not be able to load the_ tunnels\_conf.json nor the provided\_login\_info.py _configuration files_ from its folder.

As a workaround, make sure you actually goto in the executable's folder first before running it.

# Support #
If you encounter any issue with the project's contents, please report it to us either:
  * by sending us an email at `inter_team_ppe_2008 @t googlegroups.com`
  * by filing an issue in the [Issues section](http://code.google.com/p/multitunneler/issues/list) of this website.

More generally, you can contact us at `inter_team_ppe_2008 @t googlegroups.com`.