################################
### Graphistry Make & Distro ###
################################



## Environment Vars ##
#--------------------#

SHELL := /bin/bash
UMASK := $$(umask)
PLATFORM := $(shell uname)
ifeq  ($(PLATFORM),Linux)
  UID := $$(id -u $$USER)
  GID := $$(id -g $$USER)
else
  UID := 7777
  GID := 8888
endif



## Environment ##
#---------------#

env.print:
	echo "====================================="		
	echo "pwd: `pwd`"
	echo "~: `(cd ~ && pwd)`"		
	uname -a
	echo "Date :: `date`"
	cat VERSION || echo "No VERSION"
	cat CUDA_SHORT_VERSION || echo "No CUDA_SHORT_VERSION"
	md5sum --version | grep md5sum || echo "No md5sum"
	packer --version || echo "No packer"
	nvidia-smi || echo "No nvidia-smi"
	docker --version || echo "No docker"
	docker-compose --version || echo "No docker-compose"
	node --version || echo "No node"
	npm --version || echo "No npm"
	nvm --version || echo "No nvm"
	tsc --version || echo "No tsc"
	lerna --version || echo "No lerna"
	yarn --version || echo "No yarn"
	python --version || echo "No python"
	pip --version || echo "No pip"
	pip3 --version || echo "No pip3"
	python2.7 --version || echo "No python2.7"
	python3.7 --version || echo "No python3.7"
	echo "-------------- ls -al . -------------"
	ls -al .
	echo "-------------- ls -al ~ -------------"
	ls -al ~
	echo "-------------- docker images --------"
	docker images || echo "no docker"	
	echo "-------------- docker ps -a ---------"
	docker ps -a || echo "no docker"
	echo "-------------------------------------"

grype:
	curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin


## Cloud ##
#--------------------#


gha.free-space.quick:
	df -h
	echo "remove big /usr/local"
	sudo rm -rf "/usr/local/share/boost"
	sudo rm -rf /usr/local/lib/android >/dev/null 2>&1
	df -h
	sudo rm -rf /usr/share/dotnet/sdk > /dev/null 2>&1
	sudo rm -rf /usr/share/dotnet/shared > /dev/null 2>&1
	sudo rm -rf /usr/share/swift > /dev/null 2>&1
	df -h
	
gha.swap.resize:
	sudo df -h
	echo "swap info (expected: 4GB at /mnt/swapfile)"
	grep Swap /proc/meminfo
	swapon -s
	sudo ls -alh /mnt/swapfile || ( echo "expected swapfile at /mnt/swapfile" && exit 1 )
	#echo "Drop swap"
	#sudo swapoff -a
	#sudo rm -f /swapfile
	# ref. https://askubuntu.com/a/1075516/22308
	sudo swapoff /mnt/swapfile # make all swap off
	sudo rm -rf /mnt/swapfile # remove the current
	#                                    8*1024Mb=8192Mb
	sudo dd if=/dev/zero of=/swapfile bs=1M count=16384 # resize the swapfile to 16Gb
	sudo chmod 600 /swapfile
	sudo mkswap /swapfile # format the file as swap
	sudo swapon /swapfile # activate it
	sudo swapon -s        # view swap size
	echo "Swap remade!"
	echo "swap info (expected: 16Gb at /swapfile)"
	grep Swap /proc/meminfo
	swapon -s
	sudo ls -alh /swapfile || ( echo "expected swapfile at /swapfile" && exit 1 )
	sudo df -h

## Primarily for S3 container.tar.gz build action
gha.free-space.many:
	df -h
	sudo docker system df
	echo "Prune docker"
	sudo docker system prune -f -a --volumes
	sudo docker builder prune -a
	df -h
	sudo docker system df
	echo "swap info (expected: 4GB at /mnt/swapfile)"
	grep Swap /proc/meminfo
	#echo "Identiy biggest dpkg packages"
	#sudo dpkg-query --show --showformat='${Installed-Size}\t${Package}\n' | sort -rh | head -50 | awk '{print $1/1024, $2}' || echo "fail dpkg-query"
	#echo "Identify biggest apt packages"
	#sudo aptitude search "~i" --display-format "%p %I" --sort installsize | tail -50 || echo "fail apt search"
	echo "Remove apt packages"
	apt-get purge --auto-remove -y azure-cli google-cloud-sdk hhvm google-chrome-stable firefox powershell mono-devel || echo ok1
	apt-get purge --auto-remove aria2 ansible shellcheck rpm xorriso zsync \
		'clang-.*' lldb-6.0 lld-6.0 lldb-8 lld-8 \
		lldb-9 lld-9 \
		esl-erlang g++-8 g++-9 gfortran-8 gfortran-9 \
		cabal-install-2.0 cabal-install-2.2 \
		cabal-install-2.4 cabal-install-3.0 cabal-install-3.2 'gcc-.*' heroku imagemagick \
		libmagickcore-dev libmagickwand-dev libmagic-dev ant ant-optional kubectl \
		mercurial apt-transport-https mono-complete mono-devel 'mysql-.*' libmysqlclient-dev \
		mssql-tools unixodbc-dev yarn bazel chrpath libssl-dev libxft-dev \
		libfreetype6 libfreetype6-dev libfontconfig1 libfontconfig1-dev \
		php-zmq snmp pollinate libpq-dev postgresql-client ruby-full \
		sphinxsearch subversion mongodb-org -yq >/dev/null 2>&1 \
		|| echo "failed main apt-get remove2"
	df -h
	echo "Removing large packages"
	apt-get purge --autoremove -y libgl1-mesa-dri || echo "fail remove libmesa"
	apt-get purge --autoremove -y 'openjdk-.*' || echo "openjdk-11-jre-headless"
	apt-get purge --autoremove -y 'mysql-server-core.*' || echo "fail remove mysql-server"
	apt-get purge --autoremove -y r-base-core || echo "fail remove r-base-core"
	apt-get purge --auto-remove -y '^ghc.*'  || echo failghc
	apt-get purge --auto-remove -y '^dotnet-.*'  || echo faildotnet
	apt-get purge --auto-remove -y '^llvm-.*'  || echo failllvm
	apt-get purge --auto-remove -y 'php.*'  || echo failphp
	apt-get purge --auto-remove -y 'adoptopenjdk-.*' || echo 'fail jdk'
	apt-get purge --auto-remove -y 'hhvm' || echo 'fail hhvm'
	apt-get purge --auto-remove -y 'google-chrome-stable' || echo 'fail chrome'
	apt-get purge --auto-remove -y 'firefox' || echo 'fail ffox'
	apt-get purge --auto-remove -y podman 'mongo.*' || echo failmongo
	( apt-get purge --auto-remove -y 'rust' || apt-get purge --auto-remove -y 'rust.*' ) || echo "couldn't remove rust"
	sudo rm -rf /usr/share/az_* || echo "fail az cleanup"
	sudo rm -rf /usr/local/julia  || echo "fail julia cleanup"
	sudo rm -rf /opt/ghc || echo "fail ghc cleanup"
	sudo rm -rf /opt/hostedtoolcache && sudo mkdir -p /opt/hostedtoolcache
	sudo rm -rf /opt/pipx || echo "skip pipx"	
	sudo rm -rf /usr/local/bin/packer || echo "fail packer cleanup"
	sudo rm -rf /usr/local/bin/oc || echo "fail oc cleanup"
	sudo rm -rf /usr/local/bin/terraform || echo "fail terraform cleanup"
	sudo rm -rf /usr/local/bin/minikube || echo "fail minikube cleanup"
	sudo rm -rf /usr/local/bin/pulumi || echo "fail pulumi cleanup"
	sudo rm -rf /usr/local/bin/pulumi-* || echo "fail pulumi-* cleanup"
	sudo rm -rf /usr/local/graalvm || echo "fail graal cleanup"
	sudo rm -rf /usr/local/julia* || echo "fail julia cleanup"
	sudo rm -rf /usr/local/lib/android || echo "fail android cleanup"
	sudo rm -rf /usr/local/lib/heroku || echo "fail heroku cleanup"
	sudo rm -rf /usr/local/lib/node_modules || echo "fail node_modules cleanup"
	sudo rm -rf /usr/share/dotnet || echo "fail dotnet cleanup"
	sudo rm -rf /usr/share/miniconda || echo 'skip miniconda'
	sudo rm -rf /usr/share/gradle  || echo "skip gradle"
	sudo rm -rf /usr/share/gradle* || echo "fail gradle cleanup"
	sudo rm -rf /usr/share/rust || echo 'skip rust'
	sudo rm -rf /usr/share/swift || echo "fail swift cleanup"
	df -h
	( sudo apt-get install -y wajig && wajig large ) || echo "Failed installing wajig"
	sudo apt-get autoremove -y >/dev/null 2>&1
	sudo apt-get clean
	sudo apt-get autoremove -y >/dev/null 2>&1
	sudo apt-get autoclean -y >/dev/null 2>&1
	df -h
	echo "------------ remaining /usr/local/lib (1) ------------"
	sudo du -sh /usr/local/lib/* | sort -h | tail -n 20 || echo ok
	echo "------------ remaining /usr/share (1) ------------"
	sudo du -sh /usr/share/* | sort -h | tail -n 10 || echo ok
	echo "------------ remaining /usr/local (1) ------------"
	sudo du -sh /usr/local/* | sort -h | tail -n 10 || echo ok
	echo "------------ remaining /usr/local/bin (1) ------------"
	sudo du -sh /usr/local/bin/* | sort -h | tail -n 10 || echo ok
	echo "------------ remaining /opt (1) ------------"
	sudo du -sh /opt/* | sort -h | tail -n 10 || echo ok
	echo "https://github.com/actions/virtual-environments/issues/709"
	sudo rm -rf "$AGENT_TOOLSDIRECTORY"
	echo "------------ remaining /usr/share ------------"
	du -sh /usr/share/* | sort -h || echo ok
	echo "------------ remaining /usr/local ------------"
	du -sh /usr/local/* | sort -h || echo ok
	echo "------------ remaining /usr/local/bin --------"
	du -sh /usr/local/bin/* | sort -h || echo ok
	echo "------------ remaining /opt ------------"
	sudo du -sh /opt/* | sort -h || echo ok
	echo "------------ remaining /opt/hostedtoolcache/* ------------"
	sudo du -sh /opt/hostedtoolcache/* | sort -h || echo ok hosted
	df -h
	sudo docker info
	sudo docker system df
	sudo ls -alh /var/lib/docker || echo 'ok docker'
	sudo ls -alh /var/lib/docker/buildkit || echo 'ok docker buildkit'
