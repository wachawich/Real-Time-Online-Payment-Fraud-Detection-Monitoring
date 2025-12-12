FROM golang:1.21 AS builder

ENV GOPROXY=https://goproxy.io,direct

WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o /fiber-app

FROM debian:stable-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /fiber-app /usr/local/bin/fiber-app
EXPOSE 5000
ENTRYPOINT ["/usr/local/bin/fiber-app"]
