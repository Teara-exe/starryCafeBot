FROM python:3

# install requirements
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copy source
#COPY . .

# execute commands
#CMD [ "python", "./your-daemon-or-script.py" ]

