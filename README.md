# IsAlive?

### Project Description
IsAlive is my first attempt to create a network management automation script with Python. This is not intended to be used in Production environments, and is purely for experimental purposes, as I wanted to try a full-scale network management automation script using Python.

## How to use
After cloning the repository, it is necessary to download the appropiate package requirements for the script to run. This can be done using `pipreqs`.

1. If pipreqs not installed:
`pip3 install pipreqs`

2. Once downloaded, change into the repository directory and generate a `requirements.txt` file:
`pipreqs .`

3. Once the `requirements.txt` has generated, run the pip command and pass the `-r` flag to read the contents of the req file:
`pip3 install -r requirements.txt`

4. Run the script:
``python3 isalive.py`



