package utils

import (
	"errors"

	"github.com/gin-gonic/gin"
)

func GetUserID(c *gin.Context) (int32, error) {
	val, exists := c.Get("userID")
	if !exists {
		return 0, errors.New("userID not found in context")
	}
	id, ok := val.(int32)
	if !ok {
		return 0, errors.New("userID invalid type")
	}
	return id, nil
}
