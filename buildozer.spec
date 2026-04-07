name: Build and Release ProMed
on: [push]

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build with Buildozer (Docker)
        run: |
          docker run --rm -v "$(pwd)":/home/user/hostcwd \
          kivy/buildozer android debug

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: bin/*.apk
          tag_name: Beta_v1.0.3_build_${{ github.run_number }}
          name: ProMed Beta v1.0.3 Build ${{ github.run_number }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
