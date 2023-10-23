FROM node:21-alpine as build

WORKDIR /app

COPY playground/package*.json ./

# install project dependencies
RUN npm install

COPY playground/ .
RUN npm run build

FROM nginx:stable-alpine as production
COPY --from=build /app/build /usr/share/nginx/html
ENTRYPOINT ["nginx", "-g", "daemon off;"]