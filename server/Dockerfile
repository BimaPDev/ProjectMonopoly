# Use the correct Go version
FROM golang:1.23 AS build

# Set working directory inside container
WORKDIR /app

# Copy Go dependencies first (for better caching)
COPY go.mod go.sum ./
RUN go mod download

# Copy the entire project (this ensures cmd/api/main.go is available)
COPY . .

# Move into the correct directory where `main.go` is located
WORKDIR /app/cmd/api

# Build the Go application
RUN go build -o backend

# Use a smaller base image for runtime
FROM ubuntu:latest
WORKDIR /app
COPY --from=build /app/cmd/api/backend .
EXPOSE 8080
CMD ["./backend"]