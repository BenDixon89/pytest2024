
## Introduction

This project consists of two main components: a producer script that sends change calculation requests to a RabbitMQ queue and a python backend service deployed on an AKS cluster. The service calculates the change, stores the transaction in a PostgreSQL database, and returns the result via another RabbitMQ queue.

### Producer Script
The producer script is designed to send change calculation requests to the `change_queue` in RabbitMQ and then listen for the calculated change on the `change_returned` queue.

### Python Backend Service

The service listens to the `change_queue` for incoming change calculation requests, calculates the change, stores the transaction in a PostgreSQL database, and sends the calculated change back to the `change_returned` queue.

## 🚀 Getting Started

### Prerequisites

-   Python 3.x
-   `pika` library for RabbitMQ communication


### Installation

1.  Clone the repository:
       `git clone https://github.com/BenDixon89/pytest2024` 
    
2.  Install the required Python packages:    
    `pip install pika` 
    

### Producer Script Usage
The producer script sends change calculation requests to RabbitMQ and waits for the response.

#### How to Run

1.  Run the script:
    

    `python producer/producer.py` 
    
2.  Enter the required inputs when prompted:
    
    -   Coin denominations as a comma-separated list (e.g., `1,2,5,10,20,50`)
    -   Purchase amount (e.g., `1.28`)
    -   Tender amount (e.g., `2.00`)
3.  The script sends the request and waits for the calculated change.
    

#### Example Output
```
Enter coin denominations as a comma-separated list (e.g., 1,2,5,10): 1,2,5,10,20,50
Enter purchase amount (e.g., 1.48): 1.28
Enter tender amount (e.g., 2.00): 2.00
[x] Sent change request
[x] Received change: [50, 20, 2]
Program exited after receiving the change.
```

### Backend Service API

  **Endpoints**:
    -   `POST /calculate-change/`: Accepts change calculation requests and returns the calculated change.
    -   `GET /health`: Health check endpoint to verify database and RabbitMQ connections.

#### API Endpoints
-   **Health Endpoint**: `http://4.158.27.163/health/`
-   **Calculate Change Endpoint**: `http://4.158.27.163/calculate-change/`

#### Calculate Change Endpoint Usage

The `calculate-change` endpoint is a POST endpoint that allows you to calculate the change for a given transaction. You provide the coin denominations, the purchase amount, and the tender amount, and the endpoint returns the calculated change.

##### Endpoint
- URL: `http://4.158.27.163/calculate-change/`
- Method: POST
- Content-Type: application/json

##### Request Body
```json
{
  "coin_denominations": [1,5,10,20,50],
  "purchase_amount": 1.22,
  "tender_amount": 2.00
}
```
##### Example Response
```json
{
    "change": [
        50,
        20,
        5,
        1,
        1,
        1
    ]
}
```

#### Health Endpoint Usage

The `health` endpoint is a GET endpoint that allows you check the health of the calculation, database and RabbitMQ services. 

##### Endpoint
- URL: `http://4.158.27.163/health/`
- Method: GET

##### Example Response
```json
{
  "calculation service": "Service running",
  "database": "Database connection successful.",
  "rabbitmq": "RabbitMQ connection successful."
}
```