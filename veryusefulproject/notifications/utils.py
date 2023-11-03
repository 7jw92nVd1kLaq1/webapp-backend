from django.contrib.auth import get_user_model

from veryusefulproject.orders.models import Order, OrderIntermediaryCandidate


MODEL_MAP = {}

USER_MODEL_MAP = {
    'User': get_user_model(),
}

ORDER_MODEL_MAP = {
    'Order': Order,
    'OrderIntermediaryCandidate': OrderIntermediaryCandidate,
}

MODEL_MAP.update(USER_MODEL_MAP)
MODEL_MAP.update(ORDER_MODEL_MAP)


def check_placeholder_substring(placeholder_substring):
    """
    Returns a tuple of the role, name, and field of the model that the placeholder 
    substring will be replaced with.
    """

    if placeholder_substring.count(":") != 2:
        raise Exception("Invalid placeholder substring.")

    role = placeholder_substring[1:placeholder_substring.find(":")]
    name = placeholder_substring[placeholder_substring.find(":") + 1:placeholder_substring.rfind(":")]
    field = placeholder_substring[placeholder_substring.rfind(":") + 1:-1]

    if not role in ["actor", "affected", "involved"]:
        raise Exception("Invalid placeholder substring.")

    if len(name) == 0 or len(field) == 0:
        raise Exception("Invalid placeholder substring.")

    return role, name, field
    

def parse_action_string(action_string):
    """
    Returns a tuple of the indexes of every curly braces and its contents for mapping 
    the models later on.
    """

    temp_action_string_parsed_result = {"indexes": []}
    list_to_return = []

    for index, character in enumerate(action_string):
        if character == '{':
            temp_action_string_parsed_result["indexes"].append(index)
        elif character == '}':
            temp_action_string_parsed_result["indexes"].append(index)
            role, name, field = check_placeholder_substring(
                action_string[
                    temp_action_string_parsed_result["indexes"][0]:temp_action_string_parsed_result["indexes"][1] + 1
                ]
            )
            temp_action_string_parsed_result["role"] = role
            temp_action_string_parsed_result["name"] = name
            temp_action_string_parsed_result["field"] = field
            temp_action_string_parsed_result.pop("indexes")
            list_to_return.append(temp_action_string_parsed_result)
            temp_action_string_parsed_result = {"indexes": []}

    return list_to_return


def stringify_notification(notification_object):
    """
    Returns a string representation of a notification.

    How does it work?
    1. Fetch the action object of a notification.
    2. Parse the "action" property of the action object, and see what needs to be
    queried, in order to compose a string representation of the notification.
    3. Query the necessary models, and compose the string representation.
    4. Return the string representation.
    """
    
    replacement_strings = []

    actor_count = 0
    affected_count = 0
    involved_count = 0

    actor = notification_object.notificationobjectactor_set.all()
    affected = notification_object.notificationobjectaffectedentity_set.all()
    involved = notification_object.notificationobjectinvolvedentity_set.all()

    action_string = notification_object.action.action
    action_string_parsed_result = parse_action_string(action_string)
    for item in action_string_parsed_result:
        if item["role"] == "actor":
            actor = MODEL_MAP[item["name"]].objects.get(id=actor[actor_count].id)
            value_for_replacement = getattr(actor, item["field"])
            replacement_strings.append(value_for_replacement)
            actor_count += 1

        elif item["role"] == "affected":
            affected = MODEL_MAP[item["name"]].objects.get(id=affected[affected_count].id)
            value_for_replacement = getattr(affected, item["field"])
            replacement_strings.append(value_for_replacement)
            affected_count += 1

        elif item["role"] == "involved":
            involved = MODEL_MAP[item["name"]].objects.get(id=involved[involved_count].id)
            value_for_replacement = getattr(involved, item["field"])
            replacement_strings.append(value_for_replacement)
            involved_count += 1
        else:
            raise Exception("Invalid role.")
    
    while action_string.find("{") != -1:
        action_string = action_string.replace(
            action_string[
                action_string.find("{"):action_string.find("}") + 1
            ],
            replacement_strings.pop(0)
        )
   
    return action_string
