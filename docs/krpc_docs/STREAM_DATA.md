# Streaming Data from the Server (kRPC Python Client)

A common use case for **kRPC** is to continuously extract data from the game.  
The naïve approach is to repeatedly call a remote procedure, for example to print the position of the active vessel:

```python
import krpc
conn = krpc.connect()
vessel = conn.space_center.active_vessel
refframe = vessel.orbit.body.reference_frame
while True:
    print(vessel.position(refframe))
```

This requires significant request/response overhead.  
kRPC provides a more efficient mechanism called **streams**.

> A stream repeatedly executes a procedure on the server (with a fixed set of argument values) and sends the result to the client.  
> Only a single message is required to establish the stream, after which the server continuously pushes data until the stream is closed.

## Basic example with `add_stream`

```python
import krpc
conn = krpc.connect()
vessel = conn.space_center.active_vessel
refframe = vessel.orbit.body.reference_frame
position = conn.add_stream(vessel.position, refframe)
while True:
    print(position())
```

`conn.add_stream()` is called once to create the stream; thereafter calling `position()` returns the most recent value.  
The stream is closed automatically when the client disconnects.

## Using a context‑manager

```python
import krpc
conn = krpc.connect()
vessel = conn.space_center.active_vessel
refframe = vessel.orbit.body.reference_frame
with conn.stream(vessel.position, refframe) as position:
    while True:
        print(position())
```

Wrapping the stream in a `with` statement guarantees it is removed from the server on exit.

## Streaming attributes

Streams work for both method calls **and** attribute accesses:

```python
import krpc
conn = krpc.connect()
vessel = conn.space_center.active_vessel
flight_info = vessel.flight()
altitude = conn.add_stream(getattr, flight_info, "mean_altitude")
while True:
    print(altitude())
```

## Managing streams

* Call the stream object to get the latest value: `value = my_stream()`.
* Stop and remove a stream explicitly with `my_stream.remove()`.
* All streams are automatically stopped when the client disconnects.

---

_Source: [kRPC Python Client documentation – “Streaming Data from the Server”](https://krpc.github.io/krpc/python/client.html#streaming-data-from-the-server)_
