package auth

import (
	"errors"
	"log"
	"os"

	"github.com/dgrijalva/jwt-go"
)

var jwtKey []byte

func init() {
	secret := os.Getenv("JWT_SECRET")
	if secret == "" {
		// In production, JWT_SECRET must be set - fail fast
		if os.Getenv("GO_ENV") == "production" || os.Getenv("GIN_MODE") == "release" {
			log.Fatal("FATAL: JWT_SECRET environment variable is required in production")
		}
		// Development fallback with warning
		log.Println("WARNING: JWT_SECRET not set, using insecure development key")
		secret = "dev_only_insecure_key_do_not_use_in_production"
	}
	jwtKey = []byte(secret)
}

type Claims struct {
	UserID int32  `json:"userID"`
	Email  string `json:"email"`
	jwt.StandardClaims
}

func VerifyToken(tokenStr string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenStr, &Claims{}, func(token *jwt.Token) (interface{}, error) {
		return jwtKey, nil
	})

	if err != nil {
		return nil, err
	}

	claims, ok := token.Claims.(*Claims)
	if !ok || !token.Valid {
		return nil, errors.New("invalid token")
	}

	return claims, nil
}
