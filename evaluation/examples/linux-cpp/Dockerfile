FROM ubuntu

RUN apt-get update && apt-get install -y libzmq1

WORKDIR /app

ADD agent/example_learner /app/

ENV NAME Learner

CMD ["./example_learner"]

