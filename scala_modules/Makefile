


style:
	sbt scalastyle
	sbt scalafmtCheck


compile:
	sbt events/compile

all:
	sbt events/assembly


clean:
	sbt clean clean-files

deploy: all
	scripts/deploy.py
