# Preludio
Inspired by the musical concept of a prelude, Preludio is a computational tool designed to predict transcription factor (TF) binding sites from promoter sequence of given genes of interests. It analyzes the regulatory sequence preceding a gene to infer the TF that may shape a gene's expression and inspires researchers to pursue promising downstream investigations of regulatory mechanisms.

# Installation of MEME suite
MEME suit contains fimo, which is the core tool that predict TF binding sites. 
* It's a Linux tool so running it requires a Linux system. If you're using Windows, you can follow the steps below to activate the Windows Subsystem for Linux (WSL). 

## Activate or reset WSL
This provides a Linux system in the Windows system
Install new Ubuntu
1. Open Windows PowerShell 
2. Install new Ubuntu: `wsl --install -d Ubuntu`
   *  Again, `Ubuntu` here is the distro name I want to install. Change to yours accordingly
   * `-d` flag stands for --distribution. It tells WSL which Linux distribution you want to install
3. A new Ubuntu window will pop out saying `Installing, this may take a few minutes...`
4. The Ubuntu window later will ask you for a new UNIX name and a new password
5. Once the window gives you your current working directory and the $ prompt, you can close the Ubuntu window and the WSL window 
6. Open the MobaXTerm -> Session -> WSL
7. Choose `Ubuntu` for `Distribution` and click OK. Now you should be able to use MobaXTerm to interact with WSL Ubuntu 

Remove previous Ubuntu 
1. Open Windows PowerShell 
2. List the distros you currently have: `wsl -l`
3. Unregister the distro you want to remove: `wsl --unregister Ubuntu`
   * `Ubuntu` is the name for the distro I want to remove. Change to yours accordingly 
4. If you only had 1 distro before, you can check the remove by `wsl -l` and it should say WSL has no installed distributions

## Install MEME suite in WSL
1. Open MobaXterm and log into the Ubuntu created
2. Update WSL environment: `sudo apt update && sudo apt upgrade -y`
3. Install dependencies: 
```
sudo apt install perl libexpat1-dev python3 python3-pip zlib1g-dev ghostscript 
sudo apt-get install autoconf automake libtool wget ant
sudo apt install build-essential libgd-dev libxml2-dev libxml-simple-perl
```
4. Download the latest version of MEME suite: `wget https://meme-suite.org/meme/meme-software/5.5.8/meme-5.5.8.tar.gz`
   * The latest version can be found here: https://meme-suite.org/meme/doc/download.html
   * Right-click on the latest distribution and copy link address. Use that link to replace the link in the command above 
5. Run the following code: 
   * Replace the version name by the specific version you're installing
   * This step will take a while and you should see lots of green `PASS` in the middle 
     * If you're only using fimo, then ensure all the fimo test are passed 
```
tar zxf meme-5.5.8.tar.gz
cd meme-5.5.8
./configure --prefix=$HOME/meme --enable-build-libxml2 --enable-build-libxslt
make
make test
make install
```
6. Add MEME suite into the HOME path
```
# Add to ~/.profile (login shells, e.g., bash -l)
printf '\n# MEME Suite\nexport MEME_HOME="$HOME/meme"\nexport PATH="$MEME_HOME/bin:$MEME_HOME/libexec/meme-5.5.8:$PATH"\n' >> ~/.profile

# Add to ~/.bashrc (interactive shells you open normally)
printf '\n# MEME Suite\nexport MEME_HOME="$HOME/meme"\nexport PATH="$MEME_HOME/bin:$MEME_HOME/libexec/meme-5.5.8:$PATH"\n' >> ~/.bashrc

# Apply now in this terminal
source ~/.profile
source ~/.bashrc
hash -r
```
7. Test the installation: `fimo --version`
   * If you can see a version number, that means the installation is successful 

# Set up WSL interpreter
PyCharm requires this step so it can use the fimo inside the WSL. This might require a Professional edition of PyCharm, but workarounds are also possible. 
1. Click on the interpreter in PyCharm → Add new interpreter → On WSL
2. PyCharm should pop out a window for New target: WSL and find your WSL 
3. Once the interpreter shows as the WSL one, you can normally install packages 
   * A test that the interpreter works normally is by running a cell with `! fimo --version`. If it shows you the version number, then that means your Windows machine can find the fimo on your WSL
   * You can use `! pwd` to know the current working directory 

# JASPAR
If you need to narrow down the motif scanning by disease type, motif scanning with the full JASPAR database first and then filter for those expressed in myeloma is recommended than filter the JASPAR database for TF expressed in myeloma and then motif scanning


# Other helpful websites
TFinder: https://tfinder-ipmc.streamlit.app/

Fimo: https://meme-suite.org/meme/doc/fimo.html