CREATE TABLE IF NOT EXISTS shirts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    price DECIMAL,
    image VARCHAR(255),
    sold_out BOOLEAN DEFAULT FALSE
);

INSERT INTO shirts (name, price, image, sold_out)
VALUES ('Camisa Polo Lacoste Blanca', 150000, 'default1.jpg', false),
       ('Camisa Polo Tommy Azul', 140000, 'default2.jpg', true);
