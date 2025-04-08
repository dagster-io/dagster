import express from "express";

const app = express();

// Statically hosted files, for example:
//
// public/images/dagster-primary-horizontal.svg -> /images/dagster-primary-horizontal.svg
//
app.use(express.static("public"));

const EXAMPLE_PAYLOAD = {
  status: "success",
  user: {
    id: "u123456",
    username: "johndoe",
    email: "john.doe@example.com",
    role: "admin",
    profile: {
      firstName: "John",
      lastName: "Doe",
      avatarUrl: "https://example.com/avatars/johndoe.jpg",
    },
  },
};

app.get("/api/example", (req, res) => res.json(EXAMPLE_PAYLOAD));

app.listen(8080, () => console.log("Server ready on port 8080."));

module.exports = app;
