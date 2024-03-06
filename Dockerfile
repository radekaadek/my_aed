# pull rocky
FROM rockylinux/rockylinux:9
WORKDIR /
# copy: aquire_data.py, requirements.txt, train_model.py, visual.py, make_predictions.py,create_main_df.py and the folder neighbourer
COPY aquire_data.py /aquire_data.py
COPY requirements.txt /requirements.txt
COPY train_model.py /train_model.py
COPY visual.py /visual.py
COPY make_predictions.py /make_predictions.py
COPY create_main_df.py /create_main_df.py
COPY neighbourer /neighbourer

RUN dnf update -y
RUN dnf install python3 python3-pip cmake git make wget gcc g++ -y

# install h3
# checkout to 4.1.0
RUN wget https://github.com/uber/h3/archive/refs/tags/v4.1.0.tar.gz
RUN tar -xvf v4.1.0.tar.gz
WORKDIR /h3-4.1.0

RUN mkdir build
WORKDIR /h3-4.1.0/build
RUN cmake -DCMAKE_BUILD_TYPE=Release ..
RUN make
RUN make install
WORKDIR /

# delete artefacts
RUN rm -rf h3-4.1.0/build

# compile the neighbourer
WORKDIR /neighbourer
RUN cmake .
RUN make
WORKDIR /

# install python packages

RUN python3 -m venv venv
RUN source venv/bin/activate
RUN pip3 install kaggle
RUN mkdir /root/.kaggle
RUN pip3 install -r requirements.txt

EXPOSE 80

# run an http server and serve the /results directory
CMD ["python3", "-m", "http.server", "80", "--directory", "/results"]


