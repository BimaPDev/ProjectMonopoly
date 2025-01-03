-- CreateTable
CREATE TABLE "Streamer" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "platform" TEXT NOT NULL,
    "avgViewers" INTEGER NOT NULL,

    CONSTRAINT "Streamer_pkey" PRIMARY KEY ("id")
);
