def route(task):

    if task == "training":
        return "cuda:1"

    return "cuda:0"