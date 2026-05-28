import asyncio
from itertools import batched

import aiohttp

from db import DbSession, open_orm, close_orm, SwapiPeople

MAX_REQUESTS = 5

async def get_people(person_id: int, http_session: aiohttp.ClientSession):
    response = await http_session.get(f'https://www.swapi.tech/api/people/{person_id}/')
    json_data = await response.json()
    return json_data

async def get_total_people(http_session: aiohttp.ClientSession):
    async with http_session.get("https://www.swapi.tech/api/people/") as response:
        json_data = await response.json()
        return json_data["total_records"]

async def insert_result(results: list[dict]):
    async with DbSession() as session:
        for people_dict in results:
            if "result" not in people_dict:
                print("Пустой ответ API:", people_dict)
                continue
            properties = people_dict['result']['properties']
            people_obj = SwapiPeople(
                birth_year=properties['birth_year'],
                eye_color=properties['eye_color'],
                gender=properties['gender'],
                hair_color=properties['hair_color'],
                homeworld=properties['homeworld'],
                mass=properties['mass'],
                name=properties['name'],
                skin_color=properties['skin_color']
            )
            session.add(people_obj)
        await session.commit()

async def main():
    await open_orm()
    async with aiohttp.ClientSession() as http_session:
        total_people = await get_total_people(http_session)
        for batch in batched(range(1, total_people + 1), MAX_REQUESTS):
            coros = [get_people(i, http_session) for i in batch]
            result = await asyncio.gather(*coros)
            asyncio.create_task(insert_result(result))
        tasks = asyncio.all_tasks()
        current_task = asyncio.current_task()
        tasks.remove(current_task)
        for task in tasks:
            await task

    await close_orm()

asyncio.run(main())