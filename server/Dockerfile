FROM golang:1.21 AS build
WORKDIR /app
COPY . .
RUN go mod download
RUN go build -o backend

FROM ubuntu:latest
WORKDIR /app
COPY --from=build /app/backend .
EXPOSE 8080
CMD ["./backend"]
