package auth

import (
	"github.com/dgrijalva/jwt-go"
)

// Load JWT secret key
var jwtKey = []byte("my_secret_key") // Replace with `os.Getenv("JWT_SECRET")` for security

// Claims struct for JWT
type Claims struct {
	Email string `json:"email"`
	jwt.StandardClaims
}

// VerifyToken parses and validates a JWT token
func VerifyToken(tokenString string) (*jwt.Token, error) {
	return jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
		return jwtKey, nil
	})
}
