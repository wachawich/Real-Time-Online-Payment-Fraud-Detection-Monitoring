package main

import (
	"fmt"
	"log"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"
	"github.com/you/fiber-app/database" // ต้องตรวจสอบให้แน่ใจว่า path ถูกต้อง
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
)


type TransactionRecord struct {
	Step             int     `json:"step"`
	Type             string  `json:"type"`
	Amount           float64 `json:"amount"`
	NameOrig         string  `json:"nameOrig"`
	OldBalanceOrg    float64 `json:"oldbalanceOrg"`
	NewBalanceOrig   float64 `json:"newbalanceOrig"`
	NameDest         string  `json:"nameDest"`
	OldBalanceDest   float64 `json:"oldbalanceDest"`
	NewBalanceDest   float64 `json:"newbalanceDest"`
	IsFraud          int     `json:"isFraud"`
	IsFlaggedFraud   int     `json:"isFlaggedFraud"`
}

type TransactionsPayload struct {
	Records []TransactionRecord `json:"records"`
}


func main() {
	// Initialize database connection
	if err := database.InitDB(); err != nil {
		log.Fatalf("❌ Database initialization failed: %v", err)
	}
	defer database.DB.Close()

	app := fiber.New()

	app.Use(cors.New(cors.Config{
		AllowOrigins: "http://localhost:3001",
	}))

	app.Get("/", func(c *fiber.Ctx) error {
		hostname, _ := os.Hostname()
		return c.JSON(fiber.Map{
			"message":  "hello from fiber",
			"hostname": hostname,
			"time":     time.Now().Format(time.RFC3339),
		})
	})

	app.Get("/health", func(c *fiber.Ctx) error {
		if err := database.DB.Ping(); err != nil {
			return c.Status(fiber.StatusServiceUnavailable).SendString("Database connection failed")
		}
		return c.SendString("OK")
	})


	app.Post("/transactions", func(c *fiber.Ctx) error {
		var payload TransactionsPayload
        
		// 1. BodyParser จะจัดการแปลง JSON เป็น Struct โดยอัตโนมัติ
		if err := c.BodyParser(&payload); err != nil {
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
				"error":   "Invalid JSON payload or data types",
				"details": err.Error(),
			})
		}

		log.Printf("Received %d transactions", len(payload.Records))

		// 2. Insert transactions into the database
        var successfulInserts int = 0
        var failedInserts int = 0
        
		for _, record := range payload.Records {
			_, err := database.DB.Exec(
				`INSERT INTO transactions (
					step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig, 
					nameDest, oldbalanceDest, newbalanceDest, isFraud, isFlaggedFraud
				) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)`,
				record.Step,
				record.Type,
				record.Amount,
				record.NameOrig,
				record.OldBalanceOrg,
				record.NewBalanceOrig,
				record.NameDest,
				record.OldBalanceDest,
				record.NewBalanceDest,
				record.IsFraud,
				record.IsFlaggedFraud,
			)
			if err != nil {
				log.Printf("❌ Failed to insert transaction (Type: %s, Amount: %.2f): %v", record.Type, record.Amount, err)
                failedInserts++
			} else {
                successfulInserts++
            }
		}

		// 3. ตอบกลับด้วยสรุปผลลัพธ์
		return c.JSON(fiber.Map{
			"message": "Transactions processing complete",
			"received": len(payload.Records),
            "successful_inserts": successfulInserts,
            "failed_inserts": failedInserts,
		})
	})
    // ----------------------------------------------------


	// port จาก env หรือ default 5000
	port := 5000
	if p := os.Getenv("PORT"); p != "" {
		if pi, err := strconv.Atoi(p); err == nil {
			port = pi
		}
	}

	// run server in goroutine so we can gracefully shutdown
	go func() {
		log.Printf("✅ Server starting on port :%d", port)
		if err := app.Listen(fmt.Sprintf(":%d", port)); err != nil {
			log.Fatalf("🛑 Fiber Listen error: %v", err)
		}
	}()

	// graceful shutdown on SIGINT/SIGTERM
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	log.Println("⬇️ Shutting down server...")
	_ = app.Shutdown()
	log.Println("🛑 Server stopped")
}