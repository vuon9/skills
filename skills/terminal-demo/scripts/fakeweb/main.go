// fakeweb answers the app's web requests during a recording with made-up files.
// setup.py writes each answer to <root>/<host>/<path>; a path ending in / is
// served from __index. Inside the container the real hostnames point here,
// over HTTPS signed by a CA fakeweb makes at startup. Every request is logged
// as HIT or MISS, so a run can prove nothing went unanswered.
package main

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"fmt"
	"log"
	"math/big"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

func cert(caPath string, hosts []string) tls.Certificate {
	caKey, _ := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	ca := &x509.Certificate{SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: "terminal-demo CA"},
		NotBefore: time.Now().Add(-time.Hour), NotAfter: time.Now().Add(24 * time.Hour),
		IsCA: true, KeyUsage: x509.KeyUsageCertSign, BasicConstraintsValid: true}
	caDER, _ := x509.CreateCertificate(rand.Reader, ca, ca, &caKey.PublicKey, caKey)
	os.WriteFile(caPath, pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: caDER}), 0o644)
	caCert, _ := x509.ParseCertificate(caDER)
	key, _ := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	leaf := &x509.Certificate{SerialNumber: big.NewInt(2), Subject: pkix.Name{CommonName: hosts[0]}, DNSNames: hosts,
		NotBefore: time.Now().Add(-time.Hour), NotAfter: time.Now().Add(24 * time.Hour),
		KeyUsage: x509.KeyUsageDigitalSignature, ExtKeyUsage: []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth}}
	der, _ := x509.CreateCertificate(rand.Reader, leaf, caCert, &key.PublicKey, caKey)
	return tls.Certificate{Certificate: [][]byte{der}, PrivateKey: key}
}

func main() {
	if len(os.Args) != 4 {
		log.Fatal("usage: fakeweb <web root> <ca.pem out> <request log>")
	}
	root, caPath, logPath := os.Args[1], os.Args[2], os.Args[3]
	entries, err := os.ReadDir(root)
	if err != nil {
		log.Fatal(err)
	}
	var hosts []string
	for _, e := range entries {
		hosts = append(hosts, e.Name())
	}
	logf, err := os.OpenFile(logPath, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		log.Fatal(err)
	}
	srv := &http.Server{Addr: ":443", TLSConfig: &tls.Config{Certificates: []tls.Certificate{cert(caPath, hosts)}},
		Handler: http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			p := r.URL.Path
			if strings.HasSuffix(p, "/") {
				p += "__index"
			}
			file := filepath.Join(root, r.Host, filepath.FromSlash(p))
			body, err := os.ReadFile(file)
			if err != nil || strings.Contains(r.URL.Path, "..") {
				fmt.Fprintf(logf, "MISS %s %s%s\n", r.Method, r.Host, r.URL.RequestURI())
				http.NotFound(w, r)
				return
			}
			fmt.Fprintf(logf, "HIT %s %s%s\n", r.Method, r.Host, r.URL.RequestURI())
			if strings.Contains(p, "/manifests/") {
				w.Header().Set("Content-Type", "application/vnd.oci.image.index.v1+json")
			} else {
				w.Header().Set("Content-Type", "application/json")
			}
			w.Write(body)
		})}
	log.Fatal(srv.ListenAndServeTLS("", ""))
}
