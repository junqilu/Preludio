# Preludio
Inspired by the musical concept of a prelude, Preludio is a computational tool designed to predict transcription factor (TF) binding sites in promoter regions of genes of interest in specific cell types. By integrating motif scanning with cell-line or cell-type-specific expression data, Preludio helps researchers prioritize candidate regulatory factors for downstream investigation of gene regulatory mechanisms within the biological context of interest. 
![UCSC_example.png](readme_images/UCSC_example.png)

# Prereq
## Installation of MEME suite
MEME suit contains fimo, which is the core tool that predict TF binding sites. 
* It's a Linux tool so running it requires a Linux system. If you're using Windows, you can follow the steps below to activate the Windows Subsystem for Linux (WSL). 

### Activate or reset WSL
This provides a Linux system in the Windows system
Install new Ubuntu
1. Open Windows PowerShell 
1. Install new Ubuntu: `wsl --install -d Ubuntu`
   *  Again, `Ubuntu` here is the distro name I want to install. Change to yours accordingly
   * `-d` flag stands for --distribution. It tells WSL which Linux distribution you want to install
1. A new Ubuntu window will pop out saying `Installing, this may take a few minutes...`
1. The Ubuntu window later will ask you for a new UNIX name and a new password
1. Once the window gives you your current working directory and the $ prompt, you can close the Ubuntu window and the WSL window 
1. Open the MobaXTerm -> Session -> WSL
1. Choose `Ubuntu` for `Distribution` and click OK. Now you should be able to use MobaXTerm to interact with WSL Ubuntu 

Remove previous Ubuntu 
1. Open Windows PowerShell 
1. List the distros you currently have: `wsl -l`
1. Unregister the distro you want to remove: `wsl --unregister Ubuntu`
   * `Ubuntu` is the name for the distro I want to remove. Change to yours accordingly 
1. If you only had 1 distro before, you can check the remove by `wsl -l` and it should say WSL has no installed distributions

### Install MEME suite in WSL
1. Open MobaXterm and log into the Ubuntu created
1. Update WSL environment: `sudo apt update && sudo apt upgrade -y`
1. Install dependencies: 
```
sudo apt install perl libexpat1-dev python3 python3-pip zlib1g-dev ghostscript 
sudo apt-get install autoconf automake libtool wget ant
sudo apt install build-essential libgd-dev libxml2-dev libxml-simple-perl
```
1. Download the latest version of MEME suite: `wget https://meme-suite.org/meme/meme-software/5.5.8/meme-5.5.8.tar.gz`
   * The latest version can be found here: https://meme-suite.org/meme/doc/download.html
   * Right-click on the latest distribution and copy link address. Use that link to replace the link in the command above 
1. Run the following code: 
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
1. Add MEME suite into the HOME path
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
1. Test the installation: `fimo --version`
   * If you can see a version number, that means the installation is successful 

## Set up WSL interpreter in PyCharm 
PyCharm requires this step so it can use the fimo inside the WSL. This might require a Professional edition of PyCharm, but workarounds are also possible. 
1. Click on the interpreter in PyCharm → Add new interpreter → On WSL
1. PyCharm should pop out a window for New target: WSL and find your WSL 
1. Once the interpreter shows as the WSL one, you can normally install packages 
   * A test that the interpreter works normally is by running a cell with `! fimo --version`. If it shows you the version number, then that means your Windows machine can find the fimo on your WSL
   * You can use `! pwd` to know the current working directory 

# JASPAR
If you need to narrow down the motif scanning by disease type, motif scanning with the full JASPAR database first and then filter for those expressed in myeloma is recommended than filter the JASPAR database for TF expressed in myeloma and then motif scanning

## Filtering workflow
Through these steps, fimo motif scanning results can be filtered for a list of TF expressed in cell lines of interests for a focused cancer or cell type 
* Image below uses melanoma brain metastasis (MBM) as the focused cancer type and astrocyte (AC) as the focused cell type.
![filtering_workflow.png](readme_images/filtering_workflow.png)
* The filtered TF list expressed in a specific cancer or cell type can then be used to filter the output from fimo motif scanning

# Steps
1. Setup WSL and isntall MEME suite following the steps mentioned above
1. Configure PyCharm to have the WSL interpreter
1. Run `test_create_jaspar_filters.ipynb` once to create the TF name list for interested cancer types or cell types
1. Follow `fimo_motif_scanning_full_jaspar.ipynb` to perform motif scanning and generate the interpreted output
   * `fimo_motif_scanning_full_jaspar.ipynb` shows how to process multiple genes at once. If you only want to do process 1 gene, you can follow `test_fimo_motif_scanning.ipynb`
1. Use domain knowledge to filter through the output list of TF to find the ones that are of interests
   * Recommended tools 
     * ENCODE: https://www.encodeproject.org/ 
       * This website contains ChIP-Seq data and can quickly test the likelihood of a TF binding to a genomic region 
     * UCSC genome browser: https://genome.ucsc.edu/
       * This website allows user to easily compare multiple ChIP-Seq tracks

# Other helpful websites
fimo: https://meme-suite.org/meme/doc/fimo.html
* Online services: https://meme-suite.org/meme/tools/fimo 

TFinder: https://tfinder-ipmc.streamlit.app/

# Licence & Citation
Copyright (c) 2026 Junqi Lu.

This tool is distributed under an MIT licence. Please consult the LICENSE file for more details.

Citation can be found on the right side menu bar of this GitHub page by clicking "Cite this repository"