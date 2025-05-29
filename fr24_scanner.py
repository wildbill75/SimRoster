import time
import random
from flightradar24 import FlightRadar24API


def get_flights_between(icao_origin, icao_dest, max_results=10):
    fr_api = FlightRadar24API()

    print("[Scanner] Récupération des vols en cours depuis Flightradar24...")
    flights = fr_api.get_flights()

    results = []
    for flight in flights:
        if not flight.origin_airport_iata or not flight.destination_airport_iata:
            continue

        if (flight.origin_airport_iata.upper() == icao_origin[-3:] and
                flight.destination_airport_iata.upper() == icao_dest[-3:]):
            results.append({
                "callsign": flight.callsign,
                "airline": flight.airline,
                "aircraft_code": flight.aircraft_code,
                "registration": flight.registration,
                "origin": flight.origin_airport_iata,
                "destination": flight.destination_airport_iata,
                "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            })

            if len(results) >= max_results:
                break

    return results


def main():
    origin = "LFPO"
    destination = "LFMN"
    print(f"[Scanner] Recherche des vols entre {origin} et {destination}...")

    flights = get_flights_between(origin, destination)

    if not flights:
        print("[Scanner] Aucun vol en cours trouvé entre ces deux aéroports.")
    else:
        print(f"[Scanner] {len(flights)} vol(s) trouvé(s) :\n")
        for flight in flights:
            print(f"→ {flight['callsign']} | {flight['airline']} | {flight['aircraft_code']} | {flight['registration']}")


if __name__ == "__main__":
    main()
