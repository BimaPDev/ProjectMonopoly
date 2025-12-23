package auth

import (
	"errors"
	"os"

	"github.com/dgrijalva/jwt-go"
)

var jwtKey = []byte(getJWTSecret())

func getJWTSecret() string {
	secret := os.Getenv("JWT_SECRET")
	if secret == "" {
		return "my_secret_key"
	}
	return secret
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
