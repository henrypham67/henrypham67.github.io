---
title: 'Rate limit'
date: 2026-03-28T16:28:59+07:00
draft: true
tags: ["system-design", "api", "scalability", "networking"]
categories: ["DevOps"]
---

## fixed window

- given an allowed amount of requests in a fixed time frame (e.g. 100 requests per user per minute)
- problems:
  - there could be more than allowed requests if utilize boundary of windows (e.g. 60 requests for last and first 10 seconds of 2 windows)

## sliding window log

- when a request is made, limiter will check whether it exceeds the amount of requests in the given window by looking at earlier requests
- each users/unique identifier will have an array of timestamp for each request
- problem: there will be a huge amount of data need to be stored

## sliding window counter

- similar to `sliding window log` but instead of store a scalar of timestamps, it stores

## token bucket

## leaky bucket
