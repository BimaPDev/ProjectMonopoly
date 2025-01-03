package analytics

import (
	"time"

	"github.com/gofiber/fiber/v2"
)

// GetBestTimeHandler - Returns the best streaming time
func GetBestTimeHandler(c *fiber.Ctx) error {
	// Example heavy computation simulation
	bestTime := time.Now().Add(3 * time.Hour).Format("3:04 PM")

	return c.JSON(fiber.Map{
		"message":   "Best streaming time calculated successfully",
		"best_time": bestTime,
	})
}
