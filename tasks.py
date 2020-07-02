import os

from invoke import task

REPO_DIR = os.path.dirname(__file__)


@task
def update_adr(c, render_puml=True):
    if render_puml:
        c.run(f"plantuml -v {REPO_DIR}/doc/adr/")
    c.run(f"adr generate toc -o {REPO_DIR}/doc/adr/.outro.md > {REPO_DIR}/doc/adr/README.md")


@task
def kind(c):
    c.run(f"kind create cluster", warn=True)
    c.run("kubectl apply -f topic_crd.yaml", warn=True)
    print("Run these commands before starting kafkarator:")
    config_command = "kubectl config view --raw --minify --context kind-kind -ojson"
    print(f"export K8S_API_SERVER=$({config_command} | jq -r '.clusters[0].cluster.server')")
    print(f"export K8S_API_CERT=$({config_command} | jq -r '.clusters[0].cluster[\"certificate-authority-data\"]')")
    print(f"export K8S_CLIENT_CERT=$({config_command} | jq -r '.users[0].user[\"client-certificate-data\"]')")
    print(f"export K8S_CLIENT_KEY=$({config_command} | jq -r '.users[0].user[\"client-key-data\"]')")
