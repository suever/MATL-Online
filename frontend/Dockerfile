FROM node:18-alpine as builder

WORKDIR /app

COPY package.json .
COPY yarn.lock .

RUN yarn install --frozen-lockfile

COPY . .

ENV NODE_ENV production

RUN yarn build

FROM nginx:1.21.0-alpine as production

ENV NODE_ENV production

COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
