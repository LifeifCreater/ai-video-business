#!/usr/bin/env ruby
# frozen_string_literal: true

require "pathname"
require "uri"

ROOT = Pathname.new(__dir__).join("..").expand_path
HTML_FILES = ROOT.glob("*.html").sort
MAX_ASSET_SIZE = 25 * 1024 * 1024
errors = []

def local_target(raw_url, source)
  return if raw_url.nil? || raw_url.empty?
  return if raw_url.match?(%r{^(?:mailto:|tel:|data:|javascript:)})
  return if raw_url.include?("' +")

  uri = URI.parse(raw_url)
  return if uri.host && uri.host != "framepact.jp"

  path = uri.path.to_s
  path = source.basename.to_s if path.empty?
  path = "index.html" if path == "/"
  path = path.delete_prefix("/")
  [ROOT.join(path).cleanpath, uri.fragment]
rescue URI::InvalidURIError
  nil
end

HTML_FILES.each do |source|
  html = source.read
  errors << "#{source.basename}: missing HTML5 doctype" unless html.start_with?("<!DOCTYPE html>")
  %w[html head body main].each do |tag|
    opening_count = html.scan(/<#{tag}(?:\s|>)/i).length
    closing_count = html.scan(%r{</#{tag}>}i).length
    errors << "#{source.basename}: unbalanced <#{tag}>" unless opening_count == 1 && closing_count == 1
  end
  errors << "#{source.basename}: must contain one h1" unless html.scan(/<h1(?:\s|>)/i).length == 1
  ids = html.scan(/\bid=["']([^"']+)["']/).flatten
  id_counts = ids.each_with_object(Hash.new(0)) { |id, counts| counts[id] += 1 }
  id_counts.each { |id, count| errors << "#{source.basename}: duplicate id ##{id}" if count > 1 }

  urls = html.scan(/\b(?:href|src|poster)=["']([^"']+)["']/).flatten
  urls.concat(html.scan(%r{https://framepact\.jp/[A-Za-z0-9_./-]+}).flatten)
  urls.concat(html.scan(/\b(?:thumbnail|video):\s*["']([^"']+)["']/).flatten)

  urls.uniq.each do |url|
    resolved = local_target(url, source)
    next unless resolved

    target, fragment = resolved
    unless target.file?
      errors << "#{source.basename}: missing #{url}"
      next
    end
    next unless fragment && target.extname == ".html"

    target_ids = target.read.scan(/\bid=["']([^"']+)["']/).flatten
    errors << "#{source.basename}: missing fragment #{url}" unless target_ids.include?(fragment)
  end
end

sitemap = ROOT.join("sitemap.xml").read
sitemap_paths = sitemap.scan(%r{<loc>https://framepact\.jp(/[^<]*)</loc>}).flatten.map do |path|
  path == "/" ? "index.html" : path.delete_prefix("/")
end
indexable_pages = HTML_FILES.reject do |file|
  file.basename.to_s == "404.html" || file.read.match?(/<meta name="robots" content="noindex/i)
end.map { |file| file.basename.to_s }
(indexable_pages - sitemap_paths).each { |page| errors << "sitemap.xml: missing #{page}" }
(sitemap_paths - indexable_pages).each { |page| errors << "sitemap.xml: unexpected #{page}" }

ROOT.glob("**/*").select(&:file?).each do |file|
  next if file.to_s.include?("/.git/")
  errors << "#{file.relative_path_from(ROOT)} exceeds 25 MiB" if file.size > MAX_ASSET_SIZE
end

index = ROOT.join("index.html").read
errors << "Hero must use /videos/framepact-hero.mp4" unless index.include?('<source src="/videos/framepact-hero.mp4"')
hero_section = index[/<section class="hero">.*?<\/section>/m].to_s
errors << "Showreel must not be used by Hero" if hero_section.include?("framepact-showreel.mp4")

if errors.empty?
  puts "Site checks passed (#{HTML_FILES.length} HTML files)."
else
  warn errors.join("\n")
  exit 1
end
