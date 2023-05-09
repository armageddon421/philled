board_conf = [
    {
        "mac": b'4\x85\x18\x06\xfd\xa1',
        "name": "philled1",
        "channels": [
            [0, 10]
            ],
        "peers": ["philled2"]
    },
    {   
        "mac": b'4\x85\x18\x06\xfe\xf9',
        "name": "philled2",
        "channels": [
            [1, 10]
            ],
        "peers": ["philled1", "philled3"]
    },
    {   
        "mac": b'4\x85\x18\x05\x87\xc9',
        "name": "philled3",
        "channels": [
            [2, 10]
            ],
        "peers": ["philled2"]
    }
]