import krpc
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Default to localhost if IP environment variable is not set
IP = os.getenv("IP")

try:
    conn = krpc.connect(
        name="Test",
        address=IP,
        rpc_port=8075,
        stream_port=8076,
    )
except Exception as e:
    print(f"Error connecting to kRPC server: {e}")
    print(f"Make sure KSP is running with kRPC server enabled at {IP}:8075")
    sys.exit(1)

vsl = conn.space_center.active_vessel
body = vsl.orbit.body


# fairing1 = vsl.parts.fairings[0]
# fairing2 = vsl.parts.fairings[1]

# print(f"Fairings: {len(vsl.parts.fairings)}")

# for fairing in vsl.parts.fairings:
#     fairing.jettison()


#     if part.title == "Mothra Aerodynamic Fairing":
#         print(f"Part title: {part.title}")

#         # Find the decoupler module
#         for module in part.modules:
#             if module.name == "ModuleDecouple":
#                 print(f"Found decoupler module: {module.name}")
#                 # Trigger the decouple event
#                 print("Triggering decouple event...")
#                 module.trigger_event("Decouple")
#                 print("Decouple event triggered")
#     if part.title == "G-01 Fairing Half":
#         print(f"Part title: {part.title}")

#         # Find the decoupler module
#         for module in part.modules:
#             if module.name == "ModuleDecouple":
#                 print(f"Found decoupler module: {module.name}")
#                 # Trigger the decouple event
#                 print("Triggering decouple event...")
#                 module.trigger_event("Decouple")
#                 print("Decouple event triggered")

# for part in vsl.parts.all:
#     print(part.title)
#     if part.title == "RA-2 Relay Antenna":
#         print(f"Part title: {part.title}")

#         # Find the antenna module
#         for module in part.modules:
#             if module.name == "ModuleRTAntenna":
#                 print(f"Found antenna module: {module.name}")
#                 # Get current status
#                 print(f"Current status: {module.get_field('Status')}")
#                 # Activate the antenna
#                 print("Activating antenna...")
#                 module.set_action("Activate")
#                 print("Antenna activated")
#                 # Get new status
#                 print(f"New status: {module.get_field('Status')}")


# print(f"Antennas: {len(vsl.parts.antennas)}")
# for antenna in vsl.parts.antennas:
#     print(antenna.title)
# print(fairing1)
# print(fairing2)


def get_part_info(vessel, part_title):
    """
    Get events, actions, and fields for a specific part.

    Args:
        vessel: The vessel object
        part_title: The title of the part to inspect

    Returns:
        dict: Dictionary containing the part's modules and their events, actions, and fields
    """
    part_info = {}

    for part in vessel.parts.all:
        if part.title == part_title:
            print(f"\nFound part: {part_title}")
            part_info[part_title] = {}

            for module in part.modules:
                module_name = module.name
                part_info[part_title][module_name] = {
                    "events": [],
                    "actions": [],
                    "fields": [],
                }

                # Get events
                for event in module.events:
                    part_info[part_title][module_name]["events"].append(event)

                # Get actions
                for action in module.actions:
                    part_info[part_title][module_name]["actions"].append(action)

                # Get fields
                for field in module.fields:
                    part_info[part_title][module_name]["fields"].append(field)

                # Print the information
                print(f"\nModule: {module_name}")
                if part_info[part_title][module_name]["events"]:
                    print("Events:")
                    for event in part_info[part_title][module_name]["events"]:
                        print(f"- {event}")
                if part_info[part_title][module_name]["actions"]:
                    print("Actions:")
                    for action in part_info[part_title][module_name]["actions"]:
                        print(f"- {action}")
                if part_info[part_title][module_name]["fields"]:
                    print("Fields:")
                    for field in part_info[part_title][module_name]["fields"]:
                        print(f"- {field}")

    return part_info


# # Example usage:
# # Get info for RA-2 Relay Antenna
# antenna_info = get_part_info(vsl, "RA-2 Relay Antenna")

# # Get info for Mothra Aerodynamic Fairing
# fairing_info = get_part_info(vsl, "Mothra Aerodynamic Fairing")


def control_solar_panel(vessel, part_title, action="extend"):
    """
    Control a solar panel (extend or retract).

    Args:
        vessel: The vessel object
        part_title: The title of the solar panel to control
        action: The action to perform ("extend" or "retract")
    """
    for part in vessel.parts.all:
        if part.title == part_title:
            print(f"\nFound solar panel: {part_title}")

            for module in part.modules:
                if module.name == "ModuleDeployableSolarPanel":
                    print(f"Found solar panel module: {module.name}")
                    # Get current status
                    current_status = module.get_field("Status")
                    print(f"Current status: {current_status}")

                    # Perform the requested action
                    if action.lower() == "extend":
                        if current_status == "Extended":
                            print("Solar panel is already extended")
                        else:
                            print("Extending solar panel...")
                            module.set_action("Extend Solar Panel")
                            print("Solar panel extended")
                    elif action.lower() == "retract":
                        if current_status == "Retracted":
                            print("Solar panel is already retracted")
                        else:
                            print("Retracting solar panel...")
                            module.set_action("Retract Solar Panel")
                            print("Solar panel retracted")
                    else:
                        print(f"Invalid action: {action}. Use 'extend' or 'retract'")
                        return

                    # Get new status and energy info
                    new_status = module.get_field("Status")
                    print(f"New status: {new_status}")
                    if new_status == "Extended":
                        print(f"Energy flow: {module.get_field('Energy Flow')}")
                        print(f"Sun exposure: {module.get_field('Sun Exposure')}")


# Example usage:
# Extend solar panel
# control_solar_panel(vsl, "SP-L 1x6 Photovoltaic Panels", "extend")

# Retract solar panel
# control_solar_panel(vsl, "SP-L 1x6 Photovoltaic Panels", "retract")


def control_antenna(vessel, part_title, action="activate"):
    """
    Control a relay antenna (activate or deactivate).

    Args:
        vessel: The vessel object
        part_title: The title of the antenna to control
        action: The action to perform ("activate" or "deactivate")
    """
    for part in vessel.parts.all:
        if part.title == part_title:
            print(f"\nFound antenna: {part_title}")

            for module in part.modules:
                if module.name == "ModuleRTAntenna":
                    print(f"Found antenna module: {module.name}")
                    # Get current status
                    current_status = module.get_field("Status")
                    print(f"Current status: {current_status}")

                    # Perform the requested action
                    if action.lower() == "activate":
                        if current_status == "Active":
                            print("Antenna is already active")
                        else:
                            print("Activating antenna...")
                            module.set_action("Activate")
                            print("Antenna activated")
                    elif action.lower() == "deactivate":
                        if current_status == "Inactive":
                            print("Antenna is already inactive")
                        else:
                            print("Deactivating antenna...")
                            module.set_action("Deactivate")
                            print("Antenna deactivated")
                    else:
                        print(
                            f"Invalid action: {action}. Use 'activate' or 'deactivate'"
                        )
                        return

                    # Get new status and info
                    new_status = module.get_field("Status")
                    print(f"New status: {new_status}")
                    if new_status == "Active":
                        print(f"Dish range: {module.get_field('Dish range')}")
                        print(f"Energy: {module.get_field('Energy')}")


# Example usage:
# Activate antenna
# control_antenna(vsl, "RA-2 Relay Antenna", "activate")

# Deactivate antenna
# control_antenna(vsl, "RA-2 Relay Antenna", "deactivate")

# for part in vsl.parts.all:
#     print(part.title)


from core.parts.part_control import find_and_connect_to_nearest_antenna

# get_part_info(vsl, "Communotron HG-55")

find_and_connect_to_nearest_antenna(conn, vsl)
