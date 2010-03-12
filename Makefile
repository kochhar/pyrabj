
#
# Template makefile for data team projects
# Author: bkarlak, skochhar 
#

PROJ_NAME      :=  pyrabj
PROJ_BASEDIR   :=  $(shell pwd)
SRC_DIR        :=  $(PROJ_BASEDIR)/src
DOC_SRC_DIR    :=  $(PROJ_BASEDIR)/docs/source
BUILD_DIR      :=  $(PROJ_BASEDIR)/build
DOC_BUILD_DIR  :=  $(PROJ_BASEDIR)/docs/build
RELEASE_DIR    :=  $(BUILD_DIR)/release
BOOTSTRAP_DIR  :=  $(PROJ_BASEDIR)/bootstrap
VIRTUALENV_DIR :=  $(PROJ_BASEDIR)
BIN_DIR        :=  $(VIRTUALENV_DIR)/bin

ifeq ($(PYTHON),)
	PYTHON := python2.6
endif

MW_LIBS        := 

THIRDPARTY     := https://svn.metaweb.com/svn/thirdparty/trunk/

PYTHON_VERSION := python`$(PYTHON) -V 2>&1 | cut -c 8-10`
PROJ_PYTHON    :=  $(BIN_DIR)/python
PROJ_INSTALL   :=  $(BIN_DIR)/easy_install
ALLOW_HOSTS    :=  svn.metaweb.com
SETUP          :=  $(PROJ_BASEDIR)/setup.py
SETUPOPTS      :=  -q -f $(THIRDPARTY) --allow-hosts $(ALLOW_HOSTS) --always-unzip
TAGOPTS        :=  --tag-build .dev --tag-svn-revision
RELEASEOPTS    :=  -d $(RELEASE_DIR)

all : echo

bootstrap: build/.build_dir build/.virtualenv build/.symlinks
	@echo "@@@: Bootstrap complete"

develop: bootstrap libs .echodir
	export PYTHONPATH=$(BOOTSTRAP_DIR); $(PROJ_PYTHON) $(SETUP) develop $(SETUPOPTS)

dev-release: bootstrap develop .echodir
	export PYTHONPATH=$(BOOTSTRAP_DIR); $(PROJ_PYTHON) $(SETUP) egg_info $(TAGOPTS) sdist $(RELEASEOPTS)

libs: $(MW_LIBS)

$(MW_LIBS):
	export PYTHONPATH=$(BOOTSTRAP_DIR); cd $@ ; $(PROJ_PYTHON) $@/setup.py develop $(SETUPOPTS)

clean: clean/.symlinks
	export PYTHONPATH=$(BOOTSTRAP_DIR); $(PROJ_PYTHON) $(SETUP) develop --uninstall
	cd $(SRC_DIR); rm -rf *.egg-info
	@echo "@@@: Project cleaned, to remove virtualenv and libs try make clean-env"

clean-env: clean clean/.virtualenv clean/.build_dir
	@echo "@@@: Environment cleaned."

docs: bootstrap doclibs
	$(BIN_DIR)/sphinx-build -b html $(DOC_SRC_DIR) $(DOC_BUILD_DIR)

echo :
	@echo PROJ_NAME=$(PROJ_NAME)
	@echo PROJ_BASEDIR=$(PROJ_BASEDIR)
	@echo THIRDPARTY_DIR=$(THIRDPARTY_DIR)
	@echo BUILD_DIR=$(BUILD_DIR)
	@echo VIRTUALENV_DIR=$(VIRTUALENV_DIR)
	@echo BOOTSTRAP_DIR=$(BOOTSTRAP_DIR)
	@echo PYTHON=$(PYTHON)
	@echo PROJ_PYTHON=$(PROJ_PYTHON)
	@echo ALLOW_HOSTS=$(ALLOW_HOSTS)
	@echo SETUP=$(SETUP)
	@echo SETUPOPTS=$(SETUPOPTS)
	@echo
	@echo "Try bootstrap or develop targets"


### internal targets begin here ###
build/.build_dir:
	@echo "@@@: Creating build dir $(BUILD_DIR)"
	-mkdir -p $(BUILD_DIR)
	touch $(BUILD_DIR)/.build_dir

build/.virtualenv:
	@echo "Bootstrapping virtual python environment in $(VIRTUALENV_DIR)"
	$(PYTHON) $(BOOTSTRAP_DIR)/virtualenv.py -q --no-site-packages $(VIRTUALENV_DIR)
	touch $(BUILD_DIR)/.virtualenv

build/.symlinks: clean/.symlinks
	@echo "@@@: Installing symlinks"
	ln -s $(VIRTUALENV_DIR)/lib/$(PYTHON_VERSION)/site-packages $(PROJ_BASEDIR)/sp
	touch $(BUILD_DIR)/.symlinks

build/.doclibs:
	export PYTHONPATH=$(BOOTSTRAP_DIR); $(PROJ_INSTALL) $(SETUPOPTS) -U sphinx 
	touch $(BUILD_DIR)/.doclibs

clean/.build_dir:
	@echo "@@@: Deleting build dir $(BUILD_DIR)"
	-rm -rf $(BUILD_DIR)

clean/.virtualenv:
	@echo "@@@: Removing virtual python environment from $(VIRTUALENV_DIR)"
	-rm -rf $(VIRTUALENV_DIR)/bin
	-rm -rf $(VIRTUALENV_DIR)/lib
	-rm -rf $(VIRTUALENV_DIR)/lib64
	-rm -rf $(VIRTUALENV_DIR)/include
	-rm $(BUILD_DIR)/.virtualenv

clean/.symlinks:
	@echo "Cleaning symlinks"
	-rm $(PROJ_BASEDIR)/sp
	-rm $(BUILD_DIR)/.symlinks

.echodir:
	@echo "Setting up $(PROJ_NAME) in $(shell pwd)"

.PHONY: all bootstrap develop docs dev-release clean echo clean/.build_dir clean/.symlinks .echodir libs doclibs $(MW_LIBS)
