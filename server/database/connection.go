package database

import (
	"database/sql"
	"fmt"
	"os"

	_ "github.com/lib/pq"
)

var DB *sql.DB

func InitDB() error {
	// 1. อ่านค่าจาก Environment Variables
	user := os.Getenv("DB_USER")
	password := os.Getenv("DB_PASSWORD")
	dbname := os.Getenv("DB_NAME")
	host := os.Getenv("DB_HOST") // เพิ่มการอ่าน Host
	port := os.Getenv("DB_PORT") // เพิ่มการอ่าน Port
	sslmode := os.Getenv("DB_SSLMODE")

	if sslmode == "" {
		sslmode = "disable"
	}
    // Set default values if needed
    if host == "" { host = "localhost" }
    if port == "" { port = "5432" }

	if user == "" || password == "" || dbname == "" {
		return fmt.Errorf("database connection parameters (DB_USER, DB_PASSWORD, DB_NAME) must be set")
	}

    // --- แก้ไขจุดนี้: เพิ่ม host และ port ลงใน string ---
	connStr := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=%s", 
                            host, port, user, password, dbname, sslmode)
	
	// 2. เปิด Connection
	db, err := sql.Open("postgres", connStr)
	if err != nil {
		return fmt.Errorf("failed to open database connection: %w", err)
	}

	defer func() {
		if DB == nil {
			db.Close()
		}
	}()

	// 4. ทดสอบ Connection (Ping)
	if err := db.Ping(); err != nil {
		return fmt.Errorf("failed to ping database: %w", err)
	}

	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)

	DB = db
	return nil
}