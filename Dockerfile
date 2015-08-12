# 1. Automated build: 
# https://hub.docker.com/r/lao605/product-definition-center/builds/
# 
########################################### 
# Guide:
# 1. Use this to build a new image
# docker build -t <YOUR_NAME>/pdc <the directory your Dockerfile is located>
# 
# 2. Running the container
# 	2.1 To operate on the container interactively (with a terminal)
# 	docker run -it -p 10000:8000 <YOUR_NAME>/pdc
# 
# 	2.2 To run the container in daemon mode
# 	docker run -d -p 10000:8000 <YOUR_NAME>/pdc
# 
# 
# 3. Check the addresses
# 	3.1 Check the address of the docker machine
# 	*For Mac OS or Windows Users*
# 		docker-machine env <the name of your docker machine> --> DOCKER_HOST
# 	
# 	*For Linux Users*
# 		docker inspect <container_id> | grep IPAddress | cut -d '"' -f 4 --> DOCKER_HOST
# 
# 	3.2 Check the mapped port of your running container
# 	docker ps -l --> PORTS
# 
# 4. Access it
# Visit <DOCKER_HOST:PORTS> on your web browser
# 
# 

FROM fedora:21
MAINTAINER Zhikun Lao <zlao@redhat.com>

LABEL Description = "product-definition-center"
LABEL Vendor = "Red Hat"
LABEL Version = "0.5"

# patternfly1
RUN curl https://copr.fedoraproject.org/coprs/patternfly/patternfly1/repo/fedora-21/patternfly-patternfly1-fedora-21.repo > /etc/yum.repos.d/patternfly-patternfly1-fedora-21.repo

# solve dependencies
RUN yum -y upgrade && yum install -y \
rpm-build \
sudo \
passwd \
tar \
git \
make \
gcc \
libuuid-devel \
python-devel \
python-setuptools \
python-pip swig \
krb5-devel \
koji \
python-mock \
python-ldap \
python-requests \
patternfly1 \
vim-enhanced


# add runtime user (username and password are both `dev`) and add to sudoer
RUN useradd dev
RUN echo "dev" | passwd dev --stdin
RUN echo "dev    ALL=(ALL) ALL" >> /etc/sudoers
ENV HOME /home/dev

USER dev
RUN git clone https://github.com/release-engineering/product-definition-center ${HOME}/product-definition-center

# install and test
USER root
WORKDIR ${HOME}/product-definition-center
# specify version of djangorestframework specifically to avoid mistake...
RUN pip install djangorestframework==3.1.3
RUN make install
RUN make test

USER dev
RUN python manage.py migrate

# change setting
USER dev
WORKDIR ${HOME}/product-definition-center/pdc
RUN cp settings_local.py.dist settings_local.py
RUN echo "DEBUG = True" >> settings_local.py

# set up `virtualenv + virtualenvwrapper`
USER root
RUN curl -sL https://raw.githubusercontent.com/brainsik/virtualenv-burrito/master/virtualenv-burrito.sh | $SHELL

# container start as user `dev`
USER dev
WORKDIR ${HOME}

EXPOSE 8000

# CMD ["python", "product-definition-center/manage.py", "runserver", "0.0.0.0:8000"]
CMD ["/bin/bash"]