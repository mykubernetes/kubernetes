podTemplate(
    label: "kubernetes",
    namespace: "go-demo-3-build",
    serviceAccount: "build",
    yaml: """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: kubectl
    image: aishangwei/kubectl
    command: ["sleep"]
    args: ["100000"]
  - name: oc
    image: aishangwei/openshift-client
    command: ["sleep"]
    args: ["100000"]
  - name: golang
    image: golang:1.9
    command: ["sleep"]
    args: ["100000"]
  - name: helm
    image: aishangwei/helm:2.8.2
    command: ["sleep"]
    args: ["100000"]
"""
) {
    node("kubernetes") {
        container("kubectl") {
            stage("kubectl") {
                sh "kubectl version"
            }
        }
        container("oc") {
            stage("oc") {
                sh "oc version"
            }
        }
        container("golang") {
            stage("golang") {
                sh "go version"
            }
        }
        container("helm") {
            stage("helm") {
                sh "helm version --tiller-namespace go-demo-3-build"
            }
        }
    }
}
