


style:
	sbt scalastyle
	sbt scalafmtCheck


all:
	sbt events/assembly


clean:
	sbt clean clean-files

deploy: all
	scripts/deploy.py
