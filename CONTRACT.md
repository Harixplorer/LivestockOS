# LivestockOS Backend Contract Specification

This document details the reverse-engineered API and data contract between the LivestockOS frontend (`/app`) and the backend service (`/backend`).

---

## 1. Domain Entities & Fields

### User / Farmer (`users`)
Represents an authenticated user/farmer managing a livestock herd.
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | String (UUID) | Unique user identifier |
| `email` | String | Unique email address for JWT login |
| `hashed_password` | String | Bcrypt-hashed password |
| `full_name` | String | Farmer's display name (e.g., "Maria Garcia") |
| `phone_number` | String | Farmer's contact/mobile number |
| `role` | String | Role: `FARMER`, `ADMIN`, or `WORKER` |
| `farm_name` | String | Name of farm or ranch (e.g., "Green Pastures") |
| `village` | String | Village/locality |
| `district` | String | District/county |
| `state` | String | State/province |
| `is_active` | Boolean | Account status |
| `created_at` | Timestamp (UTC) | Creation timestamp |
| `updated_at` | Timestamp (UTC) | Last profile update |

### Animal (`animals`)
Represents an individual animal in the herd.
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | String (UUID) | Unique animal identifier (e.g. `animal-001`) |
| `farmer_id` | String (UUID) | Owner user ID (multi-tenant isolation) |
| `tag_id` | String | Ear tag / RFID identifier (e.g. `TAG-1001`) |
| `name` | String | Given animal name (e.g. `Gauri`, `Lakshmi`) |
| `breed` | String | Breed (e.g. `Gir`, `Sahiwal`, `Murrah Buffalo`) |
| `age` | Integer | Age in years |
| `gender` | String | `FEMALE` or `MALE` |
| `weight` | Float | Weight in kilograms |
| `status` | String | Health status: `HEALTHY`, `WARNING`, `CRITICAL`, `NOT_MONITORED` (Pending) |
| `sensor_status` | String | Sensor state: `NOT_PAIRED`, `PAIRED`, `ONLINE`, `OFFLINE` |
| `paired_sensor_id` | String (nullable) | Associated sensor device ID (e.g. `LOS-1001`) |
| `paired_sensor_name` | String (nullable) | Friendly sensor name (e.g. `LivestockOS_Sensor`) |
| `sensor_paired_at` | Timestamp (nullable)| When sensor was paired |
| `qr_code_payload` | String (nullable) | Encoded QR tag payload |
| `last_updated` | Timestamp (nullable)| Last telemetry timestamp |
| `created_at` | Timestamp (UTC) | Record creation timestamp |

### Sensor / Device (`sensors`)
Represents a physical IoT sensor (collar / ear tag) capable of BLE/GATT telemetry.
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | String (UUID) | Unique internal ID |
| `sensor_id` | String | Hardware identifier (e.g. `LOS-1001`) |
| `name` | String | Device name (e.g. `LivestockOS_Sensor`) |
| `mac_address` | String (nullable) | Hardware Bluetooth MAC |
| `battery_level` | Integer | Current battery percentage (0–100) |
| `is_active` | Boolean | Sensor operational state |
| `paired_animal_id`| String (UUID, null)| Currently paired animal |
| `created_at` | Timestamp (UTC) | Registration timestamp |

### SensorReading (`sensor_readings`)
Time-series telemetry readings recorded from sensors or mobile sync gateways.
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | String (UUID) | Unique reading ID |
| `animal_id` | String (UUID) | Target animal ID |
| `temperature` | Float | Body temperature in °C (Normal 38.0–39.3°C; Fever >39.5°C) |
| `activity_score` | Integer | Activity score (0–100) |
| `behavior` | String | Detected behavior (`Grazing`, `Resting`, `Idle`, `Ruminating`) |
| `rumination_mins`| Integer | Rumination minutes per hour (Normal 20–30 min/hr; Anomaly <10) |
| `is_anomaly` | Boolean | True if anomalous according to ML/rule engine |
| `anomaly_score` | Float | Model anomaly probability score |
| `recorded_at` | Timestamp (UTC) | Reading timestamp |

### Alert (`alerts`)
Health and system notifications triggered by sensor telemetry.
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | String (UUID) | Unique alert ID |
| `farmer_id` | String (UUID) | Owner farmer ID |
| `animal_id` | String (UUID) | Related animal ID |
| `alert_type` | String | Type code: `HIGH_FEVER`, `LOW_RUMINATION`, `INACTIVITY`, `SENSOR_OFFLINE` |
| `severity` | String | `CRITICAL`, `WARNING`, `INFO` |
| `message` | String | Human-readable alert summary |
| `is_resolved` | Boolean | True if farmer has acknowledged/resolved alert |
| `resolved_at` | Timestamp (nullable)| When alert was resolved |
| `created_at` | Timestamp (UTC) | Alert trigger timestamp |

### HealthScore (`health_scores`)
Composite evaluation score (0–100) for an animal.
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | String (UUID) | Unique health score ID |
| `animal_id` | String (UUID) | Related animal ID |
| `score` | Integer | Composite score (0–100) |
| `temp_component` | Integer | Temperature contribution points |
| `activity_component`| Integer | Activity contribution points |
| `rumination_component`| Integer | Rumination contribution points |
| `alert_penalty` | Integer | Penalty deducted for active unresolved alerts |
| `calculated_at` | Timestamp (UTC) | Score calculation timestamp |

---

## 2. API Endpoints Specification

### Authentication (`/auth`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | Register new user/farmer with email, password, profile | No |
| `POST` | `/auth/login` | Login with email/password; returns access & refresh tokens | No |
| `POST` | `/auth/refresh` | Exchange valid refresh token for a new access token | No |
| `POST` | `/auth/logout` | Invalidate refresh token | Yes (Bearer) |
| `GET` | `/auth/me` | Fetch authenticated user profile & farm details | Yes (Bearer) |

### Animals (`/api/v1/animals`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/animals` | List animals. Supports `search`, `breed`, `status`, `sort` (gender, name, tag), `page`, `page_size` | Yes (Bearer) |
| `POST` | `/api/v1/animals` | Register a new animal (starts in `NOT_MONITORED` status) | Yes (Bearer) |
| `GET` | `/api/v1/animals/{id}` | Get animal details, sensor status, and current vitals | Yes (Bearer) |
| `PUT` | `/api/v1/animals/{id}` | Update animal details | Yes (Bearer) |
| `DELETE`| `/api/v1/animals/{id}` | Remove animal record | Yes (Bearer) |
| `POST` | `/api/v1/animals/{id}/pair-sensor` | Associate a BLE sensor with this animal | Yes (Bearer) |
| `POST` | `/api/v1/animals/{id}/unpair-sensor` | Disassociate sensor (returns animal to not paired) | Yes (Bearer) |

### Sensors (`/api/v1/sensors`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/sensors` | List all sensors registered in the system | Yes (Bearer) |
| `POST` | `/api/v1/sensors` | Register a new sensor device | Yes (Bearer) |
| `GET` | `/api/v1/sensors/available` | List available unassigned sensors for pairing | Yes (Bearer) |

### Sensor Readings & Telemetry (`/api/v1/readings`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/readings` | Ingest sensor telemetry. Evaluates fever/rumination rules, updates health score, creates alerts | Yes (Bearer) |
| `GET` | `/api/v1/readings/{animal_id}` | Fetch historical readings with `limit` (default 50) and `period` (`today`, `last7Days`, `all`) | Yes (Bearer) |

### Alerts (`/api/v1/alerts`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/alerts` | List farm alerts with `severity` filter, `is_resolved` filter, and search | Yes (Bearer) |
| `GET` | `/api/v1/alerts/{id}` | Get alert details | Yes (Bearer) |
| `POST` | `/api/v1/alerts/{id}/resolve` | Mark alert as resolved | Yes (Bearer) |
| `POST` | `/api/v1/alerts/{id}/reopen` | Reopen resolved alert | Yes (Bearer) |

### Dashboard & Analytics (`/api/v1/dashboard` & `/api/v1/analytics`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/dashboard` | Aggregated dashboard: total animals, healthy, warnings, critical, pending, online sensors, quick actions | Yes (Bearer) |
| `GET` | `/api/v1/analytics/summary` | Herd health stats, active alerts, attention counts | Yes (Bearer) |
| `GET` | `/api/v1/analytics/distribution` | Herd health distribution breakdown | Yes (Bearer) |
| `GET` | `/api/v1/analytics/trends` | Herd vital trends over time (24 points) | Yes (Bearer) |
| `GET` | `/api/v1/analytics/sensors` | Sensor coverage metrics (paired, not paired, online) | Yes (Bearer) |
| `GET` | `/api/v1/analytics/comparison` | Animal comparison matrix across herd | Yes (Bearer) |

### QR Lookup (`/api/v1/qr`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/qr/lookup` | Resolve animal by `query` parameter (tag ID, animal ID, or encoded payload) | Yes (Bearer) |

---

## 3. Assumptions & Sensible Defaults

1. **Authentication Mode**: While the frontend supports mobile phone OTP login in its demo shell, production backend security standards mandate email/password with JWT (access token + refresh token) as specified in Step 4. Phone number is collected during registration and can also be queried for profile restore.
2. **Multi-Tenant Scoping**: All animals, alerts, telemetry, and dashboard aggregations are strictly filtered by the authenticated user's `farmer_id`.
3. **Data Integrity for Pending Animals**: As strictly verified in frontend test `local_persistence_test.dart`, newly added animals remain in `NOT_MONITORED` state with no fake telemetry, health scores, or trend points until real readings are received.
4. **Error Response Format**: All error responses adhere to a standard JSON envelope:
   ```json
   {
     "status_code": 400,
     "message": "Error description",
     "errors": [
       {
         "field": "temperature",
         "message": "Temperature must be between 30.0 and 45.0 °C"
       }
     ]
   }
   ```
