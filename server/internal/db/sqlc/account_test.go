package db

import (
	"context"
	"database/sql"
	"testing"
	"time"

	"github.com/stretchr/testify/require" // Use testify for better test assertions
)

func TestCreateUsers(t *testing.T) {
	// Prepare the arguments for the function
	arg := CreateUsersParams{
		Username:  sql.NullString{String: "user2", Valid: true},
		Role:      sql.NullString{String: "admin2", Valid: true},
		CreatedAt: sql.NullTime{Time: time.Now().UTC(), Valid: true},
	}

	// Call the function being tested
	account, err := testQueries.CreateUsers(context.Background(), arg)

	// Assert that no error occurred
	require.NoError(t, err, "error occurred while creating account")

	// Assert that the returned account has expected values
	require.NotEmpty(t, account, "account should not be empty")
	require.Equal(t, arg.Username.String, account.Username.String, "username mismatch")
	require.Equal(t, arg.Role.String, account.Role.String, "role mismatch")
	require.WithinDuration(t, arg.CreatedAt.Time, account.CreatedAt.Time, time.Second, "created_at mismatch")
}
