#!/bin/bash
mvn clean install -Pdocker-build 1>&2
mvn package -Pdocker-build 1>&2