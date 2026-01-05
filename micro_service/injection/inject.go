package main

import (
	"encoding/json"
	"io/ioutil"
	"log"
	"net/http"
)

type AdmissionReview struct {
	APIVersion string             `json:"apiVersion"`
	Kind       string             `json:"kind"`
	Request    *AdmissionRequest  `json:"request,omitempty"`
	Response   *AdmissionResponse `json:"response,omitempty"`
}

type AdmissionRequest struct {
	UID       string            `json:"uid"`
	Kind      map[string]string `json:"kind"`
	Object    json.RawMessage   `json:"object"`
	Namespace string            `json:"namespace"`
	Operation string            `json:"operation"`
}

type AdmissionResponse struct {
	UID       string  `json:"uid"`
	Allowed   bool    `json:"allowed"`
	Patch     []byte  `json:"patch,omitempty"`
	PatchType *string `json:"patchType,omitempty"`
	Status    *Status `json:"status,omitempty"`
}

type Status struct {
	Code    int32  `json:"code"`
	Message string `json:"message,omitempty"`
}

func mutate(w http.ResponseWriter, r *http.Request) {
	body, err := ioutil.ReadAll(r.Body)
	if err != nil {
		log.Printf("Error reading body: %v", err)
		http.Error(w, "can't read body", http.StatusBadRequest)
		return
	}
	defer r.Body.Close()

	log.Printf("Received request: %s", string(body))

	var review AdmissionReview
	if err := json.Unmarshal(body, &review); err != nil {
		log.Printf("Error unmarshaling request: %v", err)
		http.Error(w, "can't unmarshal body", http.StatusBadRequest)
		return
	}

	responseVersion := "admission.k8s.io/v1"
	if review.APIVersion != "" {
		responseVersion = review.APIVersion
	}

	patch := []map[string]interface{}{
		{
			"op":   "add",
			"path": "/spec/containers/-",
			"value": map[string]interface{}{
				"image":           "registry.cn-beijing.aliyuncs.com/wilsonchai/envoy:v1.32-latest",
				"imagePullPolicy": "IfNotPresent",
				"name":            "envoy",
				"args":            []string{"-c", "/etc/envoy/envoy.yaml"},
				"volumeMounts": []map[string]interface{}{
					{
						"mountPath": "/etc/envoy",
						"name":      "envoy-config",
					},
				},
			},
		},
		{
			"op":   "add",
			"path": "/spec/volumes/-",
			"value": map[string]interface{}{
				"configMap": map[string]interface{}{
					"defaultMode": 420,
					"name":        "envoy-config",
				},
				"name": "envoy-config",
			},
		},
	}

	patchBytes, err := json.Marshal(patch)
	if err != nil {
		log.Printf("Error marshaling patch: %v", err)
		return
	}

	patchType := "JSONPatch"

	resp := AdmissionReview{
		APIVersion: responseVersion,
		Kind:       "AdmissionReview",
		Response: &AdmissionResponse{
			UID:       review.Request.UID,
			Allowed:   true,
			Patch:     patchBytes,
			PatchType: &patchType,
		},
	}

	respBytes, err := json.Marshal(resp)
	if err != nil {
		log.Printf("Error marshaling response: %v", err)
		http.Error(w, "can't marshal response", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(respBytes)
}

func main() {
	http.HandleFunc("/mutate", mutate)

	log.Println("Webhook listening on :8443")
	log.Fatal(http.ListenAndServeTLS(
		":8443",
		"tls.crt",
		"tls.key",
		nil,
	))
}
