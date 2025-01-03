package main

import (
	"fmt"
	"log"
	"net/http"
)

func helloHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintln(w, "Hello from Go Service!")
}

func main() {
	http.HandleFunc("/", helloHandler)
	fmt.Println("Go service running on port 8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
