from kubernetes import client, config
from os import getenv
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_kube_config():
    path_to_kubeconfig_file = getenv("KUBECONFIG_PATH")
    config.load_kube_config(path_to_kubeconfig_file)