FROM centos:7

# Install nodejs
RUN yum -y update
RUN curl -sL https://rpm.nodesource.com/setup_12.x | bash -
RUN yum clean all && yum makecache fast
RUN yum install -y gcc-c++ make
RUN yum install -y nodejs

RUN npm install -g http-server

RUN mkdir -p /opt/front
COPY ./package.json /opt/front/package.json
WORKDIR /opt/front

RUN npm install -y

COPY ./tsconfig.json /opt/front/tsconfig.json
COPY ./tsconfig.paths.json /opt/front/tsconfig.paths.json
COPY ./public /opt/front/public
COPY ./src /opt/front/src

RUN npm run-script build

RUN cp /opt/front/build/index.html /opt/front/build/404.html

CMD http-server build -p 80 -g




