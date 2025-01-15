package main

import (
	"context"
	"fmt"
	"log"

	"github.com/jackc/pgx/v5/pgxpool"
)

func main() {
	// Connection string for PostgreSQL
	dsn := "postgres://postgres:0111@localhost:5432/mydb"

	// Create a connection pool
	db, err := pgxpool.New(context.Background(), dsn)
	if err != nil {
		log.Fatalf("Unable to connect to database: %v\n", err)
	}
	defer db.Close()

	fmt.Println("Connected to PostgreSQL successfully!")

	// Create a table
	_, err = db.Exec(context.Background(), `
		CREATE TABLE IF NOT EXISTS users (
			id SERIAL PRIMARY KEY,
			name VARCHAR(100) NOT NULL,
			email VARCHAR(100) UNIQUE NOT NULL,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		);
	`)

	// Insert sample data
	_, err = db.Exec(context.Background(), `
	INSERT INTO users (name, email) VALUES 
		('Alice', 'alice@example.com'),
		('Bob', 'bob@example.com');
	`)
	if err != nil {
		log.Fatalf("Failed to insert data: %v\n", err)
	}
	fmt.Println("Sample data inserted successfully!")
	if err != nil {
		log.Fatalf("Failed to create table: %v\n", err)
	}

	fmt.Println("Table created successfully!")
}
