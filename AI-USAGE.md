# AI Usage

## What I used AI for

* I used **ChatGPT Go** and **Claude Sonnet 5.0** mainly as reference and troubleshooting tools while working on the task.
* I used them to quickly check Docker, Docker Compose, PostgreSQL, Nginx, and application configuration when I got stuck or wanted to compare possible approaches.
* I also used AI to get an initial structure for some configuration files and the written documentation, which I then modified according to my actual implementation.

## What I handled from my side

* I set up the project structure, Git repository, Docker Compose services, networking, volumes, and resource limits.
* I made the final decisions on the Dockerfile, container users, service dependencies, PostgreSQL persistence, and Nginx reverse proxy configuration.
* I tested the setup myself instead of assuming that the configuration was working. This included checking `docker compose ps`, container logs, `curl` responses, `docker stats`, and the running Docker images.
* I verified that the application runs as the non-root `appuser` using `docker compose exec app whoami`.
* I specifically tested database persistence by running `docker compose down`, starting the complete stack again, and checking that the database value was retained.
* I also checked Git history for passwords, secrets, and tokens to make sure no actual credentials were committed.

## Where I had to troubleshoot or override the AI output

* During the first persistence test, the containers were started but the application was not immediately ready, and the first request returned a connection reset. I checked the actual container state and logs and waited for the services to become ready instead of treating the initial failure as a configuration problem.
* I corrected configuration details where the generated examples did not match my actual environment or the requirements of the project.
* I relied on the actual Docker output and test results for the final implementation rather than accepting AI-generated assumptions about how the stack would behave.

## Final approach

AI helped me move faster with references, troubleshooting, and initial examples, but the implementation and final validation were done by me. I verified the important DevOps requirements directly on the running environment, including container health, networking, persistence, resource limits, non-root execution, and credential handling.
