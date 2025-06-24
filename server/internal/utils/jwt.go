package utils

import (
	"errors"
	"net/http"
	"strings"

	"github.com/BimaPDev/ProjectMonopoly/internal/auth"
)

func GetUserIDFromRequest(r *http.Request) (int32, error) {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return 0, errors.New("missing Authorization header")
	}

	// Support "Bearer <token>"
	tokenStr := strings.TrimPrefix(authHeader, "Bearer ")
	if tokenStr == authHeader {
		return 0, errors.New("invalid Authorization header format")
	}

	claims, err := auth.VerifyToken(tokenStr)
	if err != nil {
		return 0, err
	}

	return claims.UserID, nil
}
